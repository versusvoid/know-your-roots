package article;

import edu.stanford.nlp.ie.crf.CRFClassifier;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.sequences.SeqClassifierFlags;
import edu.stanford.nlp.util.Pair;
import edu.stanford.nlp.util.StringUtils;

import java.io.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

import static edu.stanford.nlp.io.IOUtils.*;

/**
 * Разбивает слово из колонки FORM стандартного CoNLL файла
 * с деревом зависимости на морфемы и добавляет их в виде
 * отдельных столбцов.
 *
 * Extracts morphemes segmentation for FORM column of standart
 * CoNLL dependency tree file and append it as separate
 * corresponding columns.
 *
 * August 11 of the year 2014
 * Created by versus.
 */

public class RussianConllSegmenter {

    private static final Set<String> IGNORED_POS = new HashSet<String>(
        Arrays.asList(
            "PR",
            "COM",
            "CONJ",
            "PART",
            "P",
            "INTJ",
            "NID"
        )
    );

    private static class Writer implements Runnable {

        private final String outputFile;

        public Writer(String outputFile) {
            this.outputFile = outputFile;
        }

        @Override
        public void run() {
            try (FileWriter fileWriter = new FileWriter(outputFile);
                 BufferedWriter writer = new BufferedWriter(fileWriter)) {
                int wroteCount = 0;
                while (true) {
                    if (ALL_SUBMITTED && wroteCount == SUBMITTED_COUNT) break;

                    String sentence;
                    try {
                        sentence = SENTENCES.take();
                    } catch (InterruptedException ignored) {
                        continue;
                    }

                    writer.write(sentence);
                    writer.newLine();

                    wroteCount++;
                }
            } catch (IOException e) {
                System.err.printf("Error while writing results: %s. Aborting.. \n", e.getMessage());
                System.exit(5);
            }
        }

    }


    private static CRFClassifier<CoreLabel> classifier;
    private static final LinkedBlockingQueue<String> SENTENCES = new LinkedBlockingQueue<>();

    private static boolean ALL_SUBMITTED = false;
    private static int SUBMITTED_COUNT = 0;
    private static final AtomicInteger PROCESSED = new AtomicInteger();

    private static class Worker implements Runnable {

        private static PrintWriter printWriter;

        private final LinkedList<String> sentence;

        public Worker(LinkedList<String> sentence) {
            this.sentence = sentence;
        }

        @Override
        public void run() {
            StringBuilder newSentence = new StringBuilder();
            for (String line : sentence) {

                StringTokenizer tokenizer = new StringTokenizer(line, "\t");
                if (tokenizer.countTokens() != 10) {
                    System.err.printf("Expected 10 tokens but got %d on line:\n%s\n", tokenizer.countTokens(), line);
                    System.exit(4);
                }

                newSentence.append(tokenizer.nextToken()); // ID
                newSentence.append('\t');

                String form = tokenizer.nextToken(); // FORM
                newSentence.append(form);
                newSentence.append('\t');


                newSentence.append(tokenizer.nextToken()); // LEMMA
                newSentence.append('\t');
                newSentence.append(tokenizer.nextToken()); // CPOSTAG
                newSentence.append('\t');

                String pos = tokenizer.nextToken(); // POSTAG
                newSentence.append(pos);
                newSentence.append('\t');


                HashMap<String, String> newColumns = new HashMap<>();
                newColumns.put("прист", "_");
                newColumns.put("корень", "_");
                newColumns.put("суфф", "_");
                newColumns.put("оконч", "_");

                if (!IGNORED_POS.contains(pos)) {
                    String[] parts = form.split("[ -]");
                    for (String part : parts) {
                        if (part.length() < 2) continue;


                        List<CoreLabel> sequence = split(part);
                        List<CoreLabel> segmented = classifier.classify(sequence);

                        try {
                            for (Pair<String, String> morpheme : reconstruct(segmented)) {
                                String column = newColumns.get(morpheme.first);
                                if (column == null) continue;
                                if (column.equals("_")) {
                                    newColumns.put(morpheme.first, morpheme.second);
                                } else {
                                    newColumns.put(morpheme.first, String.join(column, "|", morpheme.second));
                                }
                            }
                        } catch (RuntimeException e) {
                            System.err.printf("Error in reconstructing word: %s\n", e.getMessage());
                            classifier.plainTextReaderAndWriter().printAnswers(segmented, printWriter);
                        }
                    }
                }



                newSentence.append(tokenizer.nextToken()); // FEATS
                newSentence.append('\t');

                for (String morphemeType : Arrays.asList("прист", "корень", "суфф", "оконч")) {
                    newSentence.append(newColumns.get(morphemeType));
                    newSentence.append('\t');
                }
                newSentence.append('\t');

                newSentence.append(tokenizer.nextToken()); // HEAD
                newSentence.append('\t');
                newSentence.append(tokenizer.nextToken()); // DEPREL
                newSentence.append('\t');
                newSentence.append(tokenizer.nextToken()); // PHEAD
                newSentence.append('\t');
                newSentence.append(tokenizer.nextToken()); // PDEPREL
                newSentence.append('\n');
            }

            SENTENCES.add(newSentence.toString());

            int processed = PROCESSED.incrementAndGet();
            if (processed % 1000 == 0) {
                System.out.println(processed);
            }
        }
    }

    public static void main(String[] args) throws IOException, ClassNotFoundException, InterruptedException {

        Properties props = StringUtils.argsToProperties(args);
        SeqClassifierFlags flags = new SeqClassifierFlags(props);

        classifier = new CRFClassifier<>(flags);
        Worker.printWriter = encodedOutputStreamPrintWriter(System.err, "utf-8", true);

        String textFile = flags.textFile;
        String loadPath = flags.loadClassifier;

        if (loadPath == null || loadPath.matches("\\s*")) {
            System.err.printf("No serialized classifier specified: %s\n", loadPath);
            System.exit(2);
        }

        classifier.loadClassifier(loadPath, props);

        if (textFile == null || textFile.matches("\\s*")) {
            System.err.println("No input file specified.");
            System.exit(3);
        }

        String outputFile;
        if (textFile.matches(".*\\.conll$")) {
            outputFile = textFile.replaceAll("\\.conll$", ".segmented.conll");
        } else {
            outputFile = textFile + ".segmented";
        }

        ExecutorService executorService =
            Executors.newFixedThreadPool(flags.multiThreadClassifier > 0? flags.multiThreadClassifier : 1);

        new Thread(new Writer(outputFile)).start();

        int sentenceNo = 1;
        try (FileReader fileReader = new FileReader(textFile);
            BufferedReader reader = new BufferedReader(fileReader)) {

            LinkedList<String> sentence = new LinkedList<>();

            String line = reader.readLine();
            while (line != null) {
                if (line.matches("\\s*")) {

                    executorService.execute(new Worker(sentence));
                    sentence = new LinkedList<>();

                    if (sentenceNo % 1000 == 0) {
                        System.out.printf("Submitted %d sentences\n", sentenceNo);
                    }

                    SUBMITTED_COUNT++;
                    sentenceNo++;
                } else {

                    sentence.add(line);
                }

                line = reader.readLine();
            }
        }
        ALL_SUBMITTED = true;

        executorService.shutdown();
        while (!executorService.isTerminated()) {
            executorService.awaitTermination(1, TimeUnit.HOURS);
        }

    }

    private static List<CoreLabel> split(String part) {
        ArrayList<CoreLabel> result = new ArrayList<>(part.length());

        for (int i = 0; i < part.length(); i++) {
            CoreLabel label = new CoreLabel();
            label.setWord(part.substring(i, i+1));
            label.set(CoreAnnotations.PositionAnnotation.class, Integer.toString(i));
            result.add(label);
        }

        return result;
    }

    private static List<Pair<String, String>> reconstruct(List<CoreLabel> coreLabels) {
        List<Pair<String, String>> result = new LinkedList<>();

        String currentPOW = null;
        StringBuilder currentPart = new StringBuilder();
        for (CoreLabel coreLabel : coreLabels) {
            String pow = coreLabel.getString(CoreAnnotations.AnswerAnnotation.class);
            if (currentPOW == null) {
                if (!pow.endsWith("_старт")) {
                    throw new RuntimeException("Word starts not from '_старт' tag.");
                }
                currentPOW = pow.substring(0, pow.length() - "_старт".length());
            } else if (!currentPOW.equals(pow)) {
                if (!pow.endsWith("_старт")) {
                    throw new RuntimeException("Part starts not from '_старт' tag.");
                }
                result.add(Pair.makePair(currentPOW, currentPart.toString()));
                currentPOW = pow.substring(0, pow.length() - "_старт".length());
                currentPart = new StringBuilder();
            }

            String letter = coreLabel.getString(CoreAnnotations.TextAnnotation.class);
            currentPart.append(letter);
        }

        result.add(Pair.makePair(currentPOW, currentPart.toString()));

        return result;
    }
    }
