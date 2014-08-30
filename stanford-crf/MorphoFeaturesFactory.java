package article;

import edu.stanford.nlp.ie.NERFeatureFactory;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.sequences.Clique;
import edu.stanford.nlp.sequences.ExactBestSequenceFinder;
import edu.stanford.nlp.sequences.FeatureFactory;
import edu.stanford.nlp.sequences.SeqClassifierFlags;
import edu.stanford.nlp.util.Generics;
import edu.stanford.nlp.util.PaddedList;
import edu.stanford.nlp.util.TypesafeMap;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.lang.reflect.Field;
import java.util.*;
import java.util.function.IntConsumer;
import java.util.stream.Collectors;

import static java.util.stream.IntStream.range;
import static java.util.stream.IntStream.rangeClosed;

/**
 * Фичи для разбиения слова на морфемы.
 *
 * Provides features for labeled morpheme segmatation.
 *
 * August 03 of the year 2014
 * Created by versus.
 */
public class MorphoFeaturesFactory<IN extends CoreLabel> extends FeatureFactory<IN> {


    Map<String, Set<String>> morphemesToTypes = new HashMap<>();

    @Override
    public void init(SeqClassifierFlags flags) {
        super.init(flags);

        for (String key : flags.props.stringPropertyNames()) {
            if (key.startsWith("morphemesFile")) {
                loadMorphemes(key.substring("morphemesFile.".length()), flags.props.getProperty(key));
            }
        }
    }

    private void loadMorphemes(String morphemeType, String fileName) {
        try (FileReader fileReader = new FileReader(fileName);
             BufferedReader reader = new BufferedReader(fileReader)) {
            String line = reader.readLine();
            while (line != null) {
                if (!line.startsWith("#")) {
                    Set<String> types = morphemesToTypes.get(line);
                    if (types == null) {
                        types = new HashSet<>();
                        morphemesToTypes.put(line, types);
                    }
                    types.add(morphemeType);
                }
                line = reader.readLine();
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    protected Collection<String> featuresC(PaddedList<IN> cInfo, int loc) {

        CoreLabel p = cInfo.get(loc - 1);
        CoreLabel c = cInfo.get(loc);
        CoreLabel n = cInfo.get(loc + 1);

        String pWord = getWord(p);
        String cWord = getWord(c);
        String nWord = getWord(n);


        ArrayList<String> features = new ArrayList<>();

        features.add(String.format("%s-%s-PWORD-WORD", pWord, cWord));
        features.add(String.format("%s-WORD", cWord));
        features.add(String.format("%s-%s-WORD-NWORD", cWord, nWord));

        int pos = Integer.parseInt(c.get(CoreAnnotations.PositionAnnotation.class));
        features.add(String.format("%d-POSITION", pos));

        features.add(String.format("%d-BACK-POSITION", cInfo.size() - pos));

        return features;
    }

    private Collection<String> featuresCpC(PaddedList<IN> cInfo, String word, int loc) {
        CoreLabel p = cInfo.get(loc - 1);
        CoreLabel c = cInfo.get(loc);
        CoreLabel n = cInfo.get(loc + 1);

        String pWord = getWord(p);
        String cWord = getWord(c);
        String nWord = getWord(n);

        ArrayList<String> features = new ArrayList<>();

        features.add(String.format("%s-%s-PWORD-WORD", pWord, cWord));
        features.add(String.format("%s-%s-WORD-NWORD", cWord, nWord));


        rangeClosed(loc + 1, word.length()).forEach(to -> {
            String morpheme = word.substring(loc, to);
            Set<String> types = morphemesToTypes.get(morpheme);
            if (types == null) return;

            features.addAll(types.stream().map(type -> String.format("START-OF-%s-TYPE-MORPHEME", type)).collect(Collectors.toList()));

            features.add(String.format("START-OF-%s-MORPHEME", morpheme));
        });
        rangeClosed(0, loc).forEach(from -> {
            String morpheme = word.substring(from, loc);
            Set<String> types = morphemesToTypes.get(morpheme);
            if (types == null) return;

            features.addAll(types.stream().map(type -> String.format("END-OF-%s-TYPE-MORPHEME", type)).collect(Collectors.toList()));

            features.add(String.format("END-OF-%s-MORPHEME", morpheme));
        });
        return features;
    }

    public Collection<String> getCliqueFeatures(PaddedList<IN> cInfo, int loc, Clique clique) {
        Collection<String> features = Generics.newHashSet();


        if (clique == cliqueC) {
            addAllInterningAndSuffixing(features, featuresC(cInfo, loc), "C");
        } else if (clique == cliqueCpC) {
            String word = recoverWord(cInfo);
            addAllInterningAndSuffixing(features, featuresCpC(cInfo, word, loc), "CpC");
        }

        return features;
    }

    private String recoverWord(PaddedList<IN> cInfo) {
        StringBuilder builder = new StringBuilder();
        range(0, cInfo.size()).forEach(loc -> builder.append(getWord(cInfo.get(loc))));

        return builder.toString();
    }
}
