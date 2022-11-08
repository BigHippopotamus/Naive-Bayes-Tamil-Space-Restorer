from src.nb_space_restorer import NBSpaceRestorer
import pandas as pd

train = pd.read_csv('sample_data/train.csv')['reference'].to_list()


# ====================
def test_one():

    my_nb = NBSpaceRestorer(
        train,
        ignore_case=True
    )