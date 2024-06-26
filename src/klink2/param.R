# Three semantic relations according to Klink-2 paper:
# relatedEquivalent - similarity relation and
# broaderGeneric and contributesTo - hierarchical relations.
# similarityLink is a temporal relation for computation of relatedEquivalent.
semantic <- c("relatedEquivalent", "broaderGeneric", "contributesTo", "similarityLink")

# Input relations taken into consideration:
# relation 1: if 2 keywords are used in the same publication
# relation 2: if 2 keywords are used by the same author in the same year
# relation 3: if 2 keywords are used in the same venue (name of journal and so on) in the same year
# relation 4: if 2 keywords are classified as belonging to the same research area in the same year
# then there is a co-occurrence in regards of corresponding relation.
relations <- c("publication", "author", "venue", "area")
quantified <- c(FALSE, FALSE, FALSE, FALSE)
rn <- length(relations)

# Verbosity level
# 0 - no messages
# 1 - main statistics per iteration
# 2 - notifications for the start and end of key procedures
# 3 - word-by-word messaging
verbosity <- 3

## Related keywords
# what is the minimum connection strength for keywords to be considered related
# during klink2 run?
# different for each input relation
# relkeyT <- c(50, 1250, 400, 175)
relkeyT <- c(2, 4, 4, 2)
# what is the minimum connection strength for keywords to be checked for ambiguousity?
# relkeyAmbig <- c(100, 2500, 800, 350)
relkeyAmbig <- c(1, 4, 2, 2)

## Metric params
# weights for linear combination of n measure (string similarity) which is based on
# longest common words, identical words, common characters, presence of acronyms
nweights <- c(1, 1, 1, 1)
# threshold for hierarchical metrics, different for each input relation
tR <- c(0.6, 0.6, 0.6, 0.1)
# threshold for hierarchical indicators, i.e. how many should point in the same direction
# (bound by number of relations)
th <- 3
# threshold for relatedEquivalent metric
# tS <- 0.95
tS <- 0.95
# threshold for relatedEquivalent indicators, i.e. how many should be positive
# (bound by number of relations)
# tre <- 3
tre <- 3
# coefficient for T metric
gamma <- 2 # must be > 0

## Clustering params; belong to [0, 1] interval.
# clustering threshold for mergeSimilarWords
merge_t <- 0.8
# clustering threshold for intersectBasedClustering
intersect_t <- 0.7
# clustering threshold for quickHierarchicalClustering
quick_t <- 0.6

## Filter params
# number of main keywords
nmain <- 20
# co-occurrence coverage by main keywords
maincover <- 0.15
