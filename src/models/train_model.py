from typing import Optional
from tqdm import tqdm
import numpy as np
import pandas as pd

# Feature selections
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold
# ROC
from sklearn.metrics import confusion_matrix, auc, plot_roc_curve

# Scores
from sklearn.metrics import f1_score, balanced_accuracy_score, precision_score, recall_score, make_scorer
# Models
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
# Resampling
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline
from matplotlib import gridspec

import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def chooseSampler(sampleMethod: Optional[str]):
    if sampleMethod == "under":
        return ("underSampler", RandomUnderSampler(sampling_strategy="majority"))

    elif sampleMethod == "over":
        return ("overSampler", SMOTE(sampling_strategy="minority"))

    elif sampleMethod == "both":
        return "overSampler", SMOTE(sampling_strategy="minority"),\
               "underSampler", RandomUnderSampler(sampling_strategy="majority")

    else:
        return None

def getPipe(model, sampleMethod: Optional[str]):
    sampler = chooseSampler(sampleMethod)
    if not (sampler):
        return Pipeline([
            ('scale', StandardScaler()),
            ("pca", PCA()),
            ('model', model)
        ])

    if len(sampler)==2:
        return Pipeline([
            ('scale', StandardScaler()),
            ("pca", PCA()),
            sampler,
            ('model', model)
        ])

    elif len(sampler)==4:
        return Pipeline([
            ('scale', StandardScaler()),
            ("pca", PCA()),
            sampler[0:2],
            sampler[2:4],
            ('model', model)
        ])

    else:
        raise ValueError("Wrong number of samplers: len(sampler)={}".format(len(sampler)))

def findParamGrid(model, numFeatures, searchPC):
    typeModel = type(model)
    if typeModel == type(RandomForestClassifier()):
        return {#"model__n_estimators": [10, 100, 1000],
                "model__max_features": ['auto'],#, 'sqrt', 'log2'],#[1, 25,50, 75, 100], #
                "model__max_depth" : np.arange(1,8),
                #"model__criterion" :['gini', 'entropy'],
                "pca__n_components": range(1,numFeatures+1, 2) if (searchPC) else [numFeatures]
                }
    elif typeModel == type(GradientBoostingClassifier()):
        return {#"model__loss":["deviance", "exponential"],
                #"model__learning_rate": [0.01, 0.025, 0.1, 0.2],
                "model__max_depth":np.arange(1,8),
                "model__max_features":['auto'],#, 'sqrt', 'log2'],#[25,50, 75, 100], #['auto', 'sqrt', 'log2'],
                #"model__criterion": ["friedman_mse", "mse"],
                #"model__subsample":[0.5, 0.75, 1],
                #"model__n_estimators":[10,100,1000],
                "pca__n_components": range(1,numFeatures+1, 2) if (searchPC) else [numFeatures]
                }
    elif typeModel == type(DecisionTreeClassifier()):
        return {"model__max_features": ['sqrt'],# 'log2'],
                #"model__min_samples_split": np.linspace(0.1, 0.5, 2),
                #"model__min_samples_leaf": np.linspace(0.1, 0.5, 2),
                "model__max_depth" : np.arange(1,8),
                #"model__ccp_alpha" : np.arange(0, 1, 0.05)
                #"model__criterion" :['gini'],#, 'entropy'],
                "pca__n_components": range(1,numFeatures+1, 2) if (searchPC) else [numFeatures]
                }
    elif typeModel == type(LogisticRegression()):#penalty{‘l1’, ‘l2’, ‘elasticnet’, ‘none’}
        return {"model__penalty":["l2"],# "l2", "elasticnet", "none"],
                "model__C": np.logspace(-3,5,7),
                "model__max_iter":[200, 400],
                "pca__n_components": range(1,numFeatures+1, 2) if (searchPC) else [numFeatures]
                }
    else:
        raise TypeError("No model has been specified: type(model):{}".format(typeModel))



def applyGridSearch(X: pd.DataFrame, y, model, cv, numPC: int, sampleMethod="None", searchPC=False):

    param_grid = findParamGrid(model, numFeatures=numPC, searchPC=searchPC)

    ## TODO: Insert these somehow in gridsearch (scoring=scoring,refit=False)
    scoring = {'accuracy':  make_scorer(balanced_accuracy_score),
               'precision': make_scorer(precision_score),
               'recall':    make_scorer(recall_score),
               'f1':        make_scorer(f1_score),
               }

    # Making a pipeline
    pipe = getPipe(model, sampleMethod)
    # Do a gridSearch
    grid = GridSearchCV(pipe, param_grid, scoring=scoring, refit="f1",
                        cv=cv,verbose=2,return_train_score=True, n_jobs=-1)
    grid.fit(X, y)
    print(grid.best_estimator_)

    return grid.best_estimator_, grid


def fitAlgorithm(classifier, trainingData, trainingTarget):
    """
    Fits a given classifier / pipeline
    """
    #train the model
    return classifier.fit(trainingData, trainingTarget)

import click

@click.command()
@click.option('--numberOfPrincipalComponents', prompt="aiwethg", default=1, help='Number of principal components.')
@click.option('--InsertApproach', prompt='Your name',
              help='The person to greet. 01-naive-approach')
def optimalize_algorithms(InsertApproach,numberOfPrincipalComponents):


    data   = pd.read_pickle(data_dir / "processed" / "processedData.pkl")
    trainingData   = pd.read_pickle(data_dir / InsertApproach / "processed" / "trainingData.pkl")
    trainingTarget= pd.read_pickle(data_dir / InsertApproach / "processed" / "trainingTarget.pkl")
    testSet       = pd.read_pickle(data_dir / InsertApproach / "processed" / "testSet.pkl")

    trainingData

    InsertAlgorithms = [LogisticRegression        (random_state = random_state, max_iter=200),
                        DecisionTreeClassifier    (random_state = random_state, max_features = "auto"),
                        RandomForestClassifier    (random_state = random_state, max_features = "auto", max_depth=6),\
                        GradientBoostingClassifier(random_state = random_state, max_features = "auto")]
    InsertAbbreviations = ["LOG", "DT", "RF", "GB"]
    InsertprettyNames   = ["Logistic regression", "Decision Tree", "Random Forest", "Gradient Boost"]

    includeSampleMethods = [""]#, "under", "over", "both"]

    numberRuns   = 5
    numberSplits = 5

    rskfold = RepeatedStratifiedKFold(n_splits=numberSplits, n_repeats=numberRuns, random_state=random_state)

    ModelsBestParams = pd.Series({}, dtype="string")

    Abbreviations = []
    prettyNames   = []
    Algorithms = []

    for i, algorithm in tqdm(enumerate(InsertAlgorithms)):
        for method in includeSampleMethods:
            print("Finding best params for: {}".format(InsertAbbreviations[i] + " " + method))
            bestEstimator, ModelsBestParams[InsertAbbreviations[i] + " " + method] = applyGridSearch(
                                                                                 X = trainingData.drop(["material_id", "full_formula"], axis=1),
                                                                                 y = trainingTarget.values.reshape(-1,),
                                                                            model = algorithm,
                                                                               cv = rskfold,
                                                                            numPC = numberOfPrincipalComponents,
                                                                     sampleMethod = method,
                                                                         searchPC = False )
            Abbreviations.append(InsertAbbreviations[i] + " " + method)
            prettyNames.append(InsertAbbreviations[i] + " " + method)
            Algorithms.append(bestEstimator)


    for abbreviation in Abbreviations:
        Summary[abbreviation]            = PredictedCandidates[abbreviation]
        Summary[abbreviation + "Prob"]   = PredictedCandidates[abbreviation + "Prob"]
        print("{} predict the number of candidates as: {}".format(abbreviation, int(np.sum(PredictedCandidates[abbreviation]))))

if __name__ == '__main__':

    optimalize_algorithms()
