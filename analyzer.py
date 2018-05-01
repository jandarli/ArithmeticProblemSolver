from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet
from stanfordcorenlp import StanfordCoreNLP
import config
from operator import itemgetter


class Entity():
    def __init__(self, owner, verb, value=0, name=''):
        """
        :param owner: Person 1 in the question
        :param verb: Verb indicating increase / decrease
        :param value: Number of entities held
        :param name: Name of the entity
        """

        self.owner = owner
        self.verb = verb
        self.value = value
        self.name = name

    def set_value(self, value):
        self.value = value

    def set_name(self, name):
        self.name = name


def extract(word_problem):
    verb = ''
    tense = ''
    keyword = ''
    entities = []
    objects = []
    word_problem = word_problem.split(' . ')
    # Create a file config.py and and set path = to path to stanford-corenlp-full-2018-02-27
    nlp = StanfordCoreNLP(config.path, memory='8g')
    nouns = []
    quantities = []
    for sentence in word_problem:
        for word in sentence.split():
            tag = nlp.pos_tag(word)[0][1]
            tag = tag.encode('ascii', 'ignore')
            if tag.startswith('V') or tag.startswith('N') or tag.startswith('R') or \
                    tag.startswith('A') or tag.startswith('S'):
                stem = WordNetLemmatizer().lemmatize(word, pos=tag[0].lower())
            else:
                stem = WordNetLemmatizer().lemmatize(word)
            if tag.find("VB") != -1 or tag.find("RBR") != -1 or tag.find("JJ") != -1:
                if tag.find("VB") != -1:
                    verb = stem.encode('ascii', 'ignore')

        parse = nlp.parse(sentence).encode('ascii', 'ignore')
        dependencies = nlp.dependency_parse(sentence)
        # (relation, source, target)
        dependencies = sorted(dependencies, key=itemgetter(1))
        # More robust way to find the tense
        if parse.find("(VP (VBD ") != -1 or parse.find("(VP (VBN ") != -1:
            tense = "past"
        elif parse.find("(VP (VBP ") != -1 or parse.find("(VP (VBG ") != -1:
            tense = "present"
        for dependency in dependencies:
            # Get the subject of the sentences
            if dependency[0].encode('ascii', 'ignore') == 'nsubj' or dependency[0].encode('ascii', 'ignore') == 'iobj':
                if nlp.pos_tag(sentence.split()[int(dependency[2] - 1)])[0][1].find("PRP") == -1:
                    nouns.append(sentence.split()[int(dependency[2] - 1)])
            # get quantities
            elif nlp.pos_tag(sentence.split()[int(dependency[2] - 1)])[0][1].find("CD") != -1:
                quantities.append(float(sentence.split()[int(dependency[2] - 1)]))
            # get objects
            # TODO: GENERALIZE ASSUMPTION ON NUMBER OF ITEMS IN QUESTION TO MORE THAN 1
            elif dependency[0].encode('ascii', 'ignore') == 'dobj':
                if nlp.pos_tag(sentence.split()[int(dependency[2] - 1)])[0][1].find("NN") != -1 or \
                        nlp.pos_tag(sentence.split()[int(dependency[2] - 1)])[0][1].find("NNS") != -1:
                    # Added stemmed versions of objects for now
                    tag = nlp.pos_tag(sentence.split()[int(dependency[2] - 1)])[0][1].encode('ascii', 'ignore')
                    if tag.startswith('V') or tag.startswith('N') or tag.startswith('R') or \
                            tag.startswith('A') or tag.startswith('S'):
                        stem = WordNetLemmatizer().lemmatize(sentence.split()[int(dependency[2] - 1)],
                                                             pos=tag[0].lower())
                    else:
                        stem = WordNetLemmatizer().lemmatize(sentence.split()[int(dependency[2] - 1)])
                    objects.append(stem.encode('ascii', 'ignore'))

    # Create entities for each subject
    for i, noun in enumerate(nouns):
        entity = Entity(noun, verb)
        try:
            entity.set_value(quantities[i])
        except IndexError:
            entity.set_value(0)
        try:
            entity.set_name(objects[i])
        except IndexError:
            # In the case of an empty object after conjunction
            entity.set_name(objects[0])
        entities.append(entity)

    nlp.close()
    return entities


