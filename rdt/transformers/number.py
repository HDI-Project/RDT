import sys

import numpy as np
import pandas as pd

from rdt.transformers.base import BaseTransformer
from rdt.transformers.null import NullTransformer


class NumberTransformer(BaseTransformer):
    """Transformer for numerical data."""

    def __init__(self, *args, **kwargs):
        """Initialize transformer."""
        super().__init__(type='number', *args, **kwargs)
        self.default_val = None
        self.subtype = None

    def fit(self, col, column_metadata=None, missing=None):
        """Prepare the transformer to convert data.

        Args:
            col(pandas.DataFrame): Data to transform.
            column_metadata(dict): Meta information of the column.
            missing(bool): Wheter or not handle missing values using NullTransformer.

        Returns:
            pandas.DataFrame
        """
        self.col_name = column_metadata['name']
        self.subtype = column_metadata['subtype']
        self.default_val = self.get_default_value(col)

    def transform(self, col, column_metadata=None, missing=None):
        """Prepare the transformer to convert data and return the processed table.

        Args:
            col(pandas.DataFrame): Data to transform.
            column_metadata(dict): Meta information of the column.
            missing(bool): Wheter or not handle missing values using NullTransformer.

        Returns:
            pandas.DataFrame
        """

        column_metadata = column_metadata or self.column_metadata
        missing = missing if missing is not None else self.missing
        self.check_data_type(column_metadata)

        out = pd.DataFrame(index=col.index)

        # if are just processing child rows, then the name is already known
        out[self.col_name] = col[self.col_name]

        # Handle missing
        if missing:
            nt = NullTransformer()
            out = nt.fit_transform(out, column_metadata)
            out[self.col_name] = out.apply(self.get_val, axis=1)
            return out

        out[self.col_name] = out.apply(self.get_val, axis=1)

        if self.subtype == 'int':
            out[self.col_name] = out[self.col_name].astype(int)

        return out

    def reverse_transform(self, col, column_metadata=None, missing=None):
        """Converts data back into original format.

        Args:
            col(pandas.DataFrame): Data to transform.
            column_metadata(dict): Meta information of the column.
            missing(bool): Wheter or not handle missing values using NullTransformer.

        Returns:
            pandas.DataFrame
        """

        column_metadata = column_metadata or self.column_metadata
        missing = missing if missing is not None else self.missing

        self.check_data_type(column_metadata)

        output = pd.DataFrame(index=col.index)
        subtype = column_metadata['subtype']
        col_name = column_metadata['name']
        fn = self.get_number_converter(col_name, subtype)

        if missing:
            new_col = col.apply(fn, axis=1)
            new_col = new_col.rename(col_name)
            data = pd.concat([new_col, col['?' + col_name]], axis=1)
            nt = NullTransformer()
            output[col_name] = nt.reverse_transform(data, column_metadata)

        else:
            output[col_name] = col.apply(fn, axis=1)

        if self.subtype == 'int':
            output[self.col_name] = output[self.col_name].astype(int)

        return output

    def get_default_value(self, data):
        """ """
        col = data[self.col_name]
        uniques = col[~col.isnull()].unique()
        if not len(uniques):
            value = 0

        else:
            value = uniques[0]

        if self.subtype == 'integer':
            value = int(value)

        return value

    def get_val(self, x):
        """Converts to int."""
        try:
            if self.subtype == 'integer':
                return int(round(x[self.col_name]))
            else:
                if np.isnan(x[self.col_name]):
                    return self.default_val

                return x[self.col_name]

        except (ValueError, TypeError):
            return self.default_val

    def get_number_converter(self, col_name, subtype):
        """Returns a converter that takes in a value and turns it into an integer, if necessary.

        Args:
            col_name(str): Name of the column.
            subtype(str): Numeric subtype of the values.

        Returns:
            function
        """

        def safe_round(x):
            val = x[col_name]
            if np.isposinf(val):
                val = sys.maxsize
            elif np.isneginf(val):
                val = -sys.maxsize
            if np.isnan(val):
                val = self.default_val
            if subtype == 'integer':
                return int(round(val))
            return val

        return safe_round
