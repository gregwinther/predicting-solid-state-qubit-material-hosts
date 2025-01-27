from pymatgen.core.periodic_table import Element
from pymatgen.analysis.local_env import VoronoiNN
import pandas as pd
import numpy as np
from typing import Optional, Iterable, Tuple, Dict
from matminer.data_retrieval.retrieve_MP import MPDataRetrieval

from src.features import featurizer
from src.data.utils import LOG
from src.features.utils.utils import clean_df
from datetime import datetime
from tqdm import tqdm

class PRESET_HEBNES_2021(featurizer.extendedMODFeaturizer):

    from matminer.featurizers.composition import (
        AtomicOrbitals,
        AtomicPackingEfficiency,
        BandCenter,
        CohesiveEnergy,
        ElectronAffinity,
        ElectronegativityDiff,
        ElementFraction,
        ElementProperty,
        IonProperty,
        Miedema,
        OxidationStates,
        Stoichiometry,
        TMetalFraction,
        ValenceOrbital,
        YangSolidSolution,
    )
    from matminer.featurizers.structure import (
        BagofBonds,
        BondFractions,
        ChemicalOrdering,
        CoulombMatrix,
        DensityFeatures,
        EwaldEnergy,
        GlobalSymmetryFeatures,
        MaximumPackingEfficiency,
        PartialRadialDistributionFunction,
        RadialDistributionFunction,
        SineCoulombMatrix,
        StructuralHeterogeneity,
        XRDPowderPattern,
    )

    from matminer.featurizers.site import (
        AGNIFingerprints,
        AverageBondAngle,
        AverageBondLength,
        BondOrientationalParameter,
        ChemEnvSiteFingerprint,
        CoordinationNumber,
        CrystalNNFingerprint,
        GaussianSymmFunc,
        GeneralizedRadialDistributionFunction,
        LocalPropertyDifference,
        OPSiteFingerprint,
        VoronoiFingerprint,
    )
    from matminer.featurizers.dos import (
        DOSFeaturizer,
    )
    from matminer.featurizers.bandstructure import (
        BandFeaturizer,
    )

    composition_featurizers = (
        AtomicOrbitals(),
        AtomicPackingEfficiency(),
        BandCenter(),
        ElementFraction(),
        ElementProperty.from_preset("magpie"),
        IonProperty(),
        Miedema(),
        Stoichiometry(),
        TMetalFraction(),
        ValenceOrbital(),
        YangSolidSolution(),
    )

    oxid_composition_featurizers = (
        ElectronegativityDiff(),
        OxidationStates(),
    )

    structure_featurizers = (
        DensityFeatures(),
        GlobalSymmetryFeatures(),
        RadialDistributionFunction(),
        CoulombMatrix(),
        #PartialRadialDistributionFunction(), #Introduces a large amount of features
        SineCoulombMatrix(),
        EwaldEnergy(),
        BondFractions(),
        StructuralHeterogeneity(),
        MaximumPackingEfficiency(),
        ChemicalOrdering(),
        XRDPowderPattern(),
    )
    site_featurizers = (
        AGNIFingerprints(),
        AverageBondAngle(VoronoiNN()),
        AverageBondLength(VoronoiNN()),
        BondOrientationalParameter(),
        ChemEnvSiteFingerprint.from_preset("simple"),
        CoordinationNumber(),
        CrystalNNFingerprint.from_preset("ops"),
        GaussianSymmFunc(),
        GeneralizedRadialDistributionFunction.from_preset("gaussian"),
        LocalPropertyDifference(),
        OPSiteFingerprint(),
        VoronoiFingerprint(),
    )

    dos_featurizers = (
        DOSFeaturizer(),
    )

    band_featurizers = (
        BandFeaturizer(),
    )
    def __init__(self, n_jobs=None):
            self._n_jobs = n_jobs

    def featurize_composition(self, df):
        """Applies the preset composition featurizers to the input dataframe,
        renames some fields and cleans the output dataframe.
        """
        df = super().featurize_composition(df)

        _orbitals = {"s": 1, "p": 2, "d": 3, "f": 4}
        df["AtomicOrbitals|HOMO_character"] = df["AtomicOrbitals|HOMO_character"].map(
            _orbitals
        )
        df["AtomicOrbitals|LUMO_character"] = df["AtomicOrbitals|LUMO_character"].map(
            _orbitals
        )

        df["AtomicOrbitals|HOMO_element"] = df["AtomicOrbitals|HOMO_element"].apply(
            lambda x: -1 if not isinstance(x, str) else Element(x).Z
        )
        df["AtomicOrbitals|LUMO_element"] = df["AtomicOrbitals|LUMO_element"].apply(
            lambda x: -1 if not isinstance(x, str) else Element(x).Z
        )

        return clean_df(df)

    def featurize_structure(self, df):
        """Applies the preset structural featurizers to the input dataframe,
        renames some fields and cleans the output dataframe.
        """
        df = super().featurize_structure(df)

        dist = df["RadialDistributionFunction|radial distribution function"].iloc[0][
            "distances"
        ][:50]
        for i, d in enumerate(dist):
            _rdf_key = "RadialDistributionFunction|radial distribution function|d_{:.2f}".format(
                d
            )
            df[_rdf_key] = df[
                "RadialDistributionFunction|radial distribution function"
            ].apply(lambda x: x["distribution"][i])

        df = df.drop("RadialDistributionFunction|radial distribution function", axis=1)

        _crystal_system = {
            "cubic": 1,
            "tetragonal": 2,
            "orthorombic": 3,
            "hexagonal": 4,
            "trigonal": 5,
            "monoclinic": 6,
            "triclinic": 7,
        }

        def _int_map(x):
            if x == np.nan:
                return 0
            elif x:
                return 1
            else:
                return 0

        df["GlobalSymmetryFeatures|crystal_system"] = df[
            "GlobalSymmetryFeatures|crystal_system"
        ].map(_crystal_system)
        df["GlobalSymmetryFeatures|is_centrosymmetric"] = df[
            "GlobalSymmetryFeatures|is_centrosymmetric"
        ].map(_int_map)

        return clean_df(df)

    def featurize_dos(self, df):
        """Applies the presetdos featurizers to the input dataframe,
        renames some fields and cleans the output dataframe.
        """

        df = super().featurize_dos(df)


        hotencodeColumns = ["DOSFeaturizer|vbm_specie_1","DOSFeaturizer|cbm_specie_1"]

        one_hot = pd.get_dummies(df[hotencodeColumns])
        df = df.drop(hotencodeColumns, axis = 1).join(one_hot)

        _orbitals = {"s": 1, "p": 2, "d": 3, "f": 4}

        df["DOSFeaturizer|vbm_character_1"] = df[
           "DOSFeaturizer|vbm_character_1"
           ].map(_orbitals)
        df["DOSFeaturizer|cbm_character_1"] = df[
           "DOSFeaturizer|cbm_character_1"
           ].map(_orbitals)

        # Splitting one feature into several floating features
        # e.g. number;number;number into three columns
        splitColumns = ["DOSFeaturizer|cbm_location_1", "DOSFeaturizer|vbm_location_1"]

        for column in splitColumns:
            try:
                newColumns = df[column].str.split(";", n = 2, expand = True)
                for i in range(0,3):
                    df[column + "_" + str(i)] = np.array(newColumns[i]).astype(np.float)
            except:
                continue
        df = df.drop(splitColumns, axis=1)
        df = df.drop(["dos"], axis=1)
        return clean_df(df)

    def featurize_bandstructure(self, df):
        """Applies the preset band structure featurizers to the input dataframe,
        renames some fields and cleans the output dataframe.
        """

        df = super().featurize_bandstructure(df)

        def _int_map(x):
            if str(x) == "False":
                return 0
            elif str(x) == "True":
                return 1

        df["BandFeaturizer|is_gap_direct"] = df[
            "BandFeaturizer|is_gap_direct"
        ].map(_int_map)


        df = df.drop(["bandstructure"], axis=1)

        return clean_df(df)


    def featurize_site(self, df):
        """Applies the preset site featurizers to the input dataframe,
        renames some fields and cleans the output dataframe.
        """

        aliases = {
            "GeneralizedRadialDistributionFunction": "GeneralizedRDF",
            "AGNIFingerprints": "AGNIFingerPrint",
            "BondOrientationalParameter": "BondOrientationParameter",
            "GaussianSymmFunc": "ChemEnvSiteFingerprint|GaussianSymmFunc",
        }
        df = super().featurize_site(df, aliases=aliases)
        df = df.loc[:, (df != 0).any(axis=0)]

        return clean_df(df)
