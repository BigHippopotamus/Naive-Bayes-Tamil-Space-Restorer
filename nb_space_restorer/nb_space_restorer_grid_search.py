import os
import time

import pandas as pd
from sklearn.model_selection import ParameterGrid

from nb_space_restorer.nb_helper import (display_or_print, load_pickle,
                                         mk_dir_if_does_not_exist, save_pickle,
                                         try_clear_output)

LOG_DF_COLS = ['i', 'L', 'lambda_', 'Precision', 'Recall', 'F-score', 'Time']

ERROR_GRID_SEARCH_EXISTS = """\
This NBSpaceRestorer already has a grid search with the name \
{grid_search_name}. Either continue the existing grid search, or choose a \
new grid search name."""
MESSAGE_SKIPPING_PARAMS = """\
Skipping parameter combination at index {i} because results \
are already in the grid search log."""
WARNING_NO_EVALUATOR = """\
Warning: Unable to import FeatureRestorationEvaluator. You will be unable to \
use grid search features. See the documentation for help.
"""

try:
    from fre import FeatureRestorationEvaluator
except ModuleNotFoundError:
    print(WARNING_NO_EVALUATOR)


# ====================
class NBSpaceRestorerGridSearch:

    # ====================
    def __init__(self, parent, **kwargs):

        self.parent = parent
        self.__dict__.update(kwargs)
        self.param_combos = list(ParameterGrid({
            'L': self.L,
            'lambda_': self.lambda_
        }))
        if hasattr(self.parent, 'root_folder'):
            if os.path.exists(self.root_folder()):
                raise ValueError(
                    ERROR_GRID_SEARCH_EXISTS.format(
                        grid_search_name=self.grid_search_name)
                )
            mk_dir_if_does_not_exist(self.root_folder())
            save_pickle(self.__dict__, self.attrs_path())
        self.run_grid_search()

    # ====================
    @classmethod
    def load(cls, parent, grid_search_name: str):

        self = cls.__new__(cls)
        self.parent = parent
        self.grid_search_name = grid_search_name
        self.__dict__ = load_pickle(self.attrs_path())
        self.run_grid_search()
        return self

    # ====================
    def run_grid_search(self):

        log_df = self.get_log_df()
        for i, parameters in enumerate(self.param_combos):
            try_clear_output()
            display_or_print(log_df)
            if len(log_df[log_df['i'] == i]) > 0:
                print(MESSAGE_SKIPPING_PARAMS.format(i=i))
                continue
            L = parameters['L']
            lambda_ = parameters['lambda_']
            print('L =', L, '; lambda_ =', lambda_)
            start_time = time.time()
            hyp = self.parent.restore(self.input, L=L, lambda_=lambda_)
            evaluator = FeatureRestorationEvaluator(
                self.ref, hyp, capitalisation=False, feature_chars=' ',
                get_wer_info_on_init=False
            )
            prf = evaluator.get_prfs()[' ']
            time_taken = time.time() - start_time
            log_df = log_df.append(
                {'i': i, 'L': L, 'lambda_': lambda_, **prf,
                 'Time': time_taken},
                ignore_index=True
            )
            if hasattr(self.parent, 'root_folder'):
                self.save_log(log_df)
            self.parent.restore_chunk.cache_clear()

    # ====================
    def root_folder(self):

        return os.path.join(
            self.parent.grid_search_path(),
            self.grid_search_name
        )

    # ====================
    def log_path(self):

        return os.path.join(self.root_folder(), 'log.csv')

    # ====================
    def attrs_path(self):

        return os.path.join(self.root_folder(), 'ATTRS.pickle')

    # ====================
    def get_log_df(self) -> pd.DataFrame:

        if hasattr(self.parent, 'root_folder'):
            log_path = self.log_path()
            if os.path.exists(log_path):
                log_df = pd.read_csv(log_path)
        try:
            return log_df
        except NameError:
            log_df = pd.DataFrame(columns=LOG_DF_COLS)
            if hasattr(self.parent, 'root_folder'):
                log_df.to_csv(log_path, index=False)
            return log_df

    # ====================
    def save_log(self, log: pd.DataFrame):

        log.to_csv(self.log_path(), index=False)

    # ====================
    def show_max(self, col: str = 'F-score'):

        log_df = self.get_log_df()
        col_vals = log_df[col].to_list()
        max_val = max(col_vals)
        max_row = log_df[log_df[col] == max_val]
        display_or_print(max_row)
