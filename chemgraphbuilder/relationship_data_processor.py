"""
Module for processing relationship data files using Dask and pandas.

This module includes the `RelationshipDataProcessor` class, which is used to
load, filter, clean, and process data files related to assay-compound relationships.
"""

import os
import glob
import dask
import dask.dataframe as dd
import pandas as pd
import concurrent.futures
import logging

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RelationshipDataProcessor:
    """
    A class to process relationship data files, filtering and augmenting the data.

    Attributes:
        path (str): The directory path where the data files are stored.
        csv_files (list): List of CSV files matching the pattern 'AID_*.csv'.
        all_data_connected (dict): A dictionary containing additional data connected to assays.
    """

    def __init__(self, path):
        """
        Initializes the RelationshipDataProcessor with the specified path.

        Args:
            path (str): The directory path containing the CSV files.
        """
        self.path = path
        self.csv_files = glob.glob(os.path.join(path, "AID_*.csv"))
        self.all_data_connected = self._load_all_data_connected('Data/AllDataConnected.csv')

    def _load_all_data_connected(self, file_path):
        """
        Loads additional data from a specified file and organizes it into a dictionary.

        Args:
            file_path (str): The path to the file containing additional data.

        Returns:
            dict: A dictionary with keys as tuples of (aid, cid, activity_outcome)
                  and values as dictionaries of additional information.
        """
        all_data_connected = {}
        ddf = dd.read_csv(file_path, blocksize=20e6)
        ddf.columns = [col.replace(' ', '_').lower() for col in ddf.columns]
        ddf = ddf.dropna(subset=['aid', 'cid'], how='any')
        partitions = ddf.to_delayed()
        ddf = ddf.repartition(partition_size=10e5)

        @dask.delayed
        def process_partition(partition):
            result = {}
            partition = partition.dropna(subset=['aid', 'cid'], how='any')
            for _, row in partition.iterrows():
                key = (int(row['aid']), int(row['cid']), row['activity_outcome'])
                result[key] = row.to_dict()
            return result

        results = dask.compute(*[process_partition(part) for part in partitions])
        for result in results:
            all_data_connected.update(result)

        # Optionally save the dictionary to a file
        with open("Data/Relationships/all_data_connected_dict.txt", "w") as file:
            for key, value in all_data_connected.items():
                file.write(f"{key}: {value}\n")

        return all_data_connected

    def _add_all_data_connected_info(self, row):
        """
        Adds additional information from all_data_connected to a row.

        Args:
            row (pd.Series): A row from a DataFrame.

        Returns:
            pd.Series: The updated row with additional data if available.
        """
        key = (int(row['aid']), int(row['cid']), row['activity_outcome'])
        if key in self.all_data_connected:
            additional_info = self.all_data_connected[key]
            for col, val in additional_info.items():
                row[col] = val
        else:
            logging.warning(f"Key {key} not found in all_data_connected.")
        return row

    def _get_filtered_columns(self):
        """
        Extracts unique column names from the CSV files and additional data.

        Returns:
            list: A list of unique column names.
        """
        all_columns = set()

        # Extract additional columns from the all_data_connected dictionary
        additional_columns = set()
        for value in self.all_data_connected.values():
            additional_columns.update(value.keys())

        def read_columns(file):
            try:
                # Read only column names from the CSV file
                df = pd.read_csv(file, nrows=0)
                return set([col.replace(' ', '_').lower() for col in df.columns])
            except Exception as e:
                logging.error(f"Error reading {file}: {e}")
                return set()

        # Use ThreadPoolExecutor for concurrent reading of columns from multiple files
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(read_columns, self.csv_files))

        for columns in results:
            all_columns.update(columns)

        all_columns.update(additional_columns)

        # Save the combined columns to a file for reference
        with open("Data/Relationships/all_columns.txt", "w") as file:
            for item in all_columns:
                file.write(f"{item}\n")

        return list(all_columns)

    def process_files(self):
        """
        Processes the CSV files by filtering, cleaning, and augmenting data.

        The processed data is saved to output files.
        """
        self._filter_and_clean_data()
        logging.info("Data filtered, cleaned, and combined successfully.")

    def _filter_and_clean_data(self):
        """
        Filters and cleans data from CSV files, then saves to output files.
        """
        output_file = os.path.join('Data/Relationships/Assay_Compound_Relationship.csv')
        compound_gene_file = os.path.join('Data/Relationships/Compound_Gene_Relationship.csv')

        if os.path.exists(output_file):
            os.remove(output_file)
        if os.path.exists(compound_gene_file):
            os.remove(compound_gene_file)

        unique_column_names = self._get_filtered_columns()+['activity']

        # Initialize output files with headers
        pd.DataFrame(columns=unique_column_names).to_csv(output_file, index=False)
        pd.DataFrame(columns=['cid', 'target_geneid', 'activity', 'aid']).to_csv(compound_gene_file, index=False)

        tasks = []
        for i, file in enumerate(self.csv_files):
            if i % 100 == 0:
                logging.info(f"Processing file {i+1}/{len(self.csv_files)}: {file}")

            tasks.append(dask.delayed(self._process_file)(file, unique_column_names, output_file, compound_gene_file))

        dask.compute(*tasks)
        logging.info(f"Processed {len(self.csv_files)} files")

    def _process_file(self, file, unique_column_names, output_file, compound_gene_file):
        """
        Processes a single CSV file, applying filtering, cleaning, and adding data.

        Args:
            file (str): The file path to the CSV file.
            unique_column_names (list): The list of unique column names to use.
            output_file (str): The path to the output file for combined data.
            compound_gene_file (str): The path to the output file for compound-gene relationships.
        """
        ddf = dd.read_csv(file, blocksize=10000, dtype={'ASSAYDATA_COMMENT': 'object'})
        ddf.columns = [col.replace(' ', '_').lower() for col in ddf.columns]
        ddf = ddf.dropna(subset=['cid'], how='any')

        # Repartition to balance memory usage and performance
        ddf = ddf.repartition(partition_size=1000)

        phenotype_cols = [col for col in ddf.columns if col.startswith('phenotype')]

        def process_partition(df):
            try:
                if isinstance(df, pd.Series):
                    df = df.to_frame().T  # Convert to DataFrame if a Series is encountered
                if df.columns.duplicated().any():
                    df = df.loc[:, ~df.columns.duplicated()]
                    logging.info("Duplicated columns removed from partition.")
                df = df.reindex(columns=unique_column_names, fill_value=pd.NA)
                df = df.dropna(subset=['aid', 'cid'], how='any')

                if not df.empty:
                    df['measured_activity'] = df[phenotype_cols].apply(lambda row: row.mode()[0] if not row.mode().empty else None, axis=1)

                    df = df.apply(self._add_all_data_connected_info, axis=1)

                    if any(col in df.columns for col in phenotype_cols) and df['activity_outcome'].notna().all():
                        df = df.groupby(['activity_outcome', 'assay_name']).apply(self.propagate_phenotype).reset_index(drop=True)

                    if 'target_geneid' not in df.columns:
                        df['target_geneid'] = pd.NA

                    if 'sid' in df.columns:
                        df['activity_url'] = df.apply(lambda row: f"https://pubchem.ncbi.nlm.nih.gov/bioassay/{row['aid']}#sid={row['sid']}", axis=1)
                    else:
                        df['activity_url'] = pd.NA

                    # Drop rows where both aid and cid are 1
                    df = df[(df['aid'] != 1) | (df['cid'] != 1)]

                    df = self._determine_labels_and_activity(df)

                    logging.info(f"Processed partition with {len(df)} rows.")
                    if not df.empty:
                        # Write the processed data to the output files
                        df.to_csv(output_file, mode='a', header=not os.path.exists(output_file), index=False)
                        df[['cid', 'target_geneid', 'activity', 'aid']].to_csv(compound_gene_file, mode='a', header=not os.path.exists(compound_gene_file), index=False)
                else:
                    logging.info("No data to process after filtering.")
            except Exception as e:
                logging.error(f"Error processing partition: {e}")

        ddf.map_partitions(process_partition).compute()

    @staticmethod
    def most_frequent(row):
        """
        Finds the most frequent value in a row, excluding NaN values.

        Args:
            row (pd.Series): A row from a DataFrame.

        Returns:
            str: The most frequent value in the row.
        """
        values = row.dropna()
        string_values = values[values.apply(lambda x: isinstance(x, str))]
        return string_values.mode()[0] if not string_values.empty else None

    @staticmethod
    def propagate_phenotype(group):
        """
        Propagates the phenotype information within a group.

        Args:
            group (pd.DataFrame): A DataFrame group.

        Returns:
            pd.DataFrame: The updated group with propagated phenotype information.
        """
        phenotype_value = group['phenotype'].dropna().unique()
        if len(phenotype_value) > 0:
            group['phenotype'] = phenotype_value[0]
        return group

    def _determine_labels_and_activity(self, merged_df):
        """
        Determines the activity labels for the data based on predefined keywords.

        Args:
            merged_df (pd.DataFrame): The DataFrame containing merged data.

        Returns:
            pd.DataFrame: The DataFrame with determined activity labels.
        """
        inhibitor_keywords = [
            'inhibition', 'reversible inhibition', 'time dependent inhibition',
            'inhibitory activity', 'time-dependent inhibition', 'time dependent irreversible inhibition',
            'inhibitory concentration', 'inhibitory effect', 'inhibitory potency',
            'concentration required to inhibit', 'competitive inhibition', 'cyp inhibition',
            'irreversible inhibition', 'mechanism based inhibition', 'mixed inhibition',
            'mixed type inhibition', 'inhibitory constant', 'antagonistic activity', 'selectivity',
            's1p4 agonists', 'small molecule antagonists', 'displacement', 'mediated midazolam 1-hydroxylation',
            'time/nadph-dependent inhibition', 'reversal inhibition', 'mechanism-based inhibition',
            'mechanism based time dependent inhibition', 'reversible competitive inhibition',
            'predictive competitive inhibition','noncompetitive inhibition', 'in vitro inhibitory',
            'in vitro inhibition', 'inhibition of', 'direct inhibition','enzyme inhibition', 'dndi',
            'inhibition assay'
        ]

        ligand_keywords = [
            'binding affinity', 'spectral binding', 'interaction with', 'bind',
            'covalent binding affinity', 'apparent binding affinity'
        ]

        inhibitor_substrate_keywords = [
            'inhibitors and substrates'
        ]

        inhibitor_activator_modulator_keywords = [
            'apoprotein formation', 'panel assay', 'eurofins-panlabs enzyme assay'
        ]

        substrate_keywords = [
            'drug metabolism', 'prodrug', 'metabolic', 'oxidation', 'substrate activity',
            'michaelis-menten', 'metabolic stability', 'bioactivation', 'drug level',
            'enzyme-mediated drug depletion', 'enzyme-mediated compound formation',
            'phenotyping', 'activity of human recombinant cyp', 'activity of recombinant cyp',
            'activity at cyp', 'enzyme-mediated drug metabolism'
        ]

        inactivator_keywords = [
            'inactivator', 'inactivation of', 'mechanism based inactivation of', 'inactivators',
            'metabolism dependent inactivation'
        ]

        activator_keywords = [
            'assay for activators', 'activation of', 'activators of'
        ]

        inducer_keywords = [
            'induction of', 'inducer', 'inducers', 'time-dependant induction'
        ]

        all_keywords = (inhibitor_keywords + ligand_keywords + inhibitor_substrate_keywords +
                        inhibitor_activator_modulator_keywords + substrate_keywords +
                        inactivator_keywords + activator_keywords + inducer_keywords)

        keyword_to_label = {
            **{keyword: 'Inhibitor' for keyword in inhibitor_keywords},
            **{keyword: 'Inhibitor/Substrate' for keyword in inhibitor_substrate_keywords},
            **{keyword: 'Inhibitor/Inducer/Modulator' for keyword in inhibitor_activator_modulator_keywords},
            **{keyword: 'Substrate' for keyword in substrate_keywords},
            **{keyword: 'Inactivator' for keyword in inactivator_keywords},
            **{keyword: 'Activator' for keyword in activator_keywords},
            **{keyword: 'Inducer' for keyword in inducer_keywords},
            **{keyword: 'Ligand' for keyword in ligand_keywords},
        }

        def determine_active_label(assay_name):
            # Determine the appropriate label based on the first keyword found in the assay name
            assay_name_lower = assay_name.lower()
            first_keyword = None
            first_position = len(assay_name_lower)

            for keyword in all_keywords:
                position = assay_name_lower.find(keyword)
                if 0 <= position < first_position:
                    first_keyword = keyword
                    first_position = position

            if first_keyword:
                return keyword_to_label[first_keyword]
            return 'Inhibitor/Inducer/Modulator'

        merged_df['activity'] = None

        # Assign the 'Inactive' label where the activity outcome is inactive
        inactive_mask = merged_df['activity_outcome'] == 'Inactive'
        merged_df.loc[inactive_mask, 'activity'] = 'Inactive'

        # Assign labels based on assay name keywords for active outcomes
        active_mask = merged_df['activity_outcome'] == 'Active'
        if active_mask.any():
            merged_df.loc[active_mask, 'activity'] = merged_df.loc[active_mask, 'assay_name'].apply(determine_active_label)
            merged_df.loc[active_mask & merged_df['activity_name'].isin(['Km', 'Drug metabolism']), 'activity'] = 'Substrate'

            substrate_pattern = r'(activity of.*oxidation)|(activity at cyp.*phenotyping)|(activity at human recombinant cyp.*formation)|(activity at recombinant cyp.*formation)'
            merged_df.loc[active_mask & merged_df['assay_name'].str.contains(substrate_pattern, case=False, regex=True), 'activity'] = 'Substrate'

            ActIndMod_pattern = r'(effect on cyp)|(effect on human recombinant cyp)|(effect on recombinant cyp)|(effect on human cyp)'
            merged_df.loc[active_mask & merged_df['assay_name'].str.contains(ActIndMod_pattern, case=False, regex=True), 'activity'] = 'Inhibitor/Inducer/Modulator'

            inducer_pattern = r'(effect on cyp.*induction)|(induction of.*)'
            merged_df.loc[active_mask & merged_df['assay_name'].str.contains(inducer_pattern, case=False, regex=True), 'activity'] = 'Inducer'

            merged_df.loc[active_mask & merged_df['activity_direction'].str.contains('decreasing', case=False), 'activity'] = 'Inhibitor'
            merged_df.loc[active_mask & merged_df['activity_direction'].str.contains('increasing', case=False), 'activity'] = 'Activator'
            merged_df.loc[active_mask & (merged_df['aid'] == 1215398), 'activity'] = 'Inactivator'

        return merged_df
