import pandas as pd
import os
import subprocess
import argparse
from pathlib import Path 

  
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir',
        type=Path,
        help='Absolute path to the location of raw CTS output')
    parser.add_argument('n_runs',
        type = int,
        default = 5,
        help='Number of CTS files to analyse')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    flaky_csv = Path(output_dir, 'flaky_tests.csv')
    all_csv = Path(output_dir, 'all_results.csv')

    output_raw = [Path(output_dir, f'output_raw_{i}.txt') for i in range(args.n_runs)]
    output_tests = [Path(output_dir, f'output_tests_{i}.txt') for i in range(args.n_runs)]
    output_summary = [Path(output_dir, f'output_summary_{i}.txt') for i in range(args.n_runs)]

    # Process raw results
    for i in range(args.n_runs):
        print(f'Processing data from run {i}...')
        process_raw_results(output_raw[i], output_tests[i], output_summary[i])

    merge_run_results(output_tests, all_csv)    

    print('Finding flaky tests...')
    find_flaky_tests(all_csv, flaky_csv)

    # Load processed results
    flaky_df = pd.read_csv(flaky_csv, sep='\t')
    all_df = pd.read_csv(all_csv, sep='\t')
    
    all_tests = all_df['test'].to_list()
    n_tests = len(all_tests)

    # Analyse results at most granular level (test x parameters)
    analyse(flaky_df, args.n_runs, n_tests)

def process_raw_results(raw_output : Path, test_output : Path, summary_output: Path):

    with open(raw_output,'r') as f:
        test_raw = f.readlines()

    tests = [x for x in test_raw if ('- pass' in x or '- fail' in x or '- skip' in x)]

    print(f'Writing test output to {test_output}')
    with open(test_output,'w') as f:
        f.writelines(tests)

    test_summary = get_test_summary(test_raw)

    print(f'Writing test summary to {summary_output}')
    with open(summary_output, 'w') as f:
        f.write(test_summary)

def get_test_summary(test_output : list[str]) -> str:
    summary = '\n'.join(test_output[-10:])
    index = summary.find('Completed in')
    if index != -1:
        summary = summary[summary.find('Completed in'):]
    else:
        summary = 'Problem obtaining summary results. Check manually'
    return summary

def result_map(raw : str) -> str:
    if ' - pass' in raw:
        return 'pass'
    if ' - fail' in raw:
        return 'fail'
    if ' - skip' in raw:
        return 'skip'

    print('Problem with result map!')
    exit()

def test_map(raw : str) -> str:
    if ' - pass' in raw:
        return raw[:raw.find(' - pass')]
    if ' - fail' in raw:
        return raw[:raw.find(' - fail')]
    if ' - skip' in raw:
        return raw[:raw.find(' - skip')]

    print('Problem with test map!')
    exit()

def merge_run_results(output_tests : list[Path], output_name : str):

    results = pd.DataFrame(columns=['test'])

    for i, file in enumerate(output_tests):

        print(f'File number {i}: {file}')

        with open(file, 'r') as f:
            raw = f.readlines()

        if len(raw) == 0:
            continue

        print(f'len(raw) = {len(raw)}')

        df = pd.DataFrame(raw, columns = [f'raw_{i}'])

        df[f'result_{i}'] = df[f'raw_{i}'].apply(result_map)
        df['test'] = df[f'raw_{i}'].apply(test_map)
        
        print('\nRun {i} results df head:')
        print(df.head(10))

        results = results.merge(df, on = 'test', how = 'outer')

        print('\nOverall results df head:')
        print(results.head(10))

    # Check that all tests are present in every run
    print(f'Results df has length: {results.shape[0]}')
    nan_mask = results.isna().any(axis=1)
    nan_rows = results[nan_mask]
    if len(nan_rows > 0):
        print(f'Tests missing from run! Number of NaN results is: {nan_rows.shape[0]}')
        print(f'NaN rows:')
        print(nan_rows)
        print(f'NaN tests:')
        for test in nan_rows['test']:
            print(test)
        print(f'Dropping NaN rows for now')
        #TODO: look into why this is happening
        results.dropna()   
        print(f'Results df now has length: {results.shape[0]}')  
    else:
        print('No tests are missing from any run')

    results['unique_results'] = list(map(set,results.filter(regex='result_*').values))
    results['unique_results'] = results['unique_results'].apply(lambda x: len(x))

    print(f'Writing all results to {output_name}')
    results.to_csv(output_name, sep='\t')

    return results

def find_flaky_tests(all_csv : Path, flaky_csv : Path) -> pd.DataFrame:

    results = pd.read_csv(all_csv, sep = '\t')

    flaky_tests = results[results['unique_results'] > 1]
    cols = flaky_tests.columns
    cols = [x for x in cols if ('raw' not in x)]
    flaky_tests = flaky_tests[cols]

    flaky_tests.to_csv(flaky_csv)

def count_pass(x : pd.Series):
    return len([i for i in x if i == 'pass'])

def count_fail(x : pd.Series):
    return len([i for i in x if i == 'fail'])

def report_results(n_flakes,
        n_runs,
        n_tests,
        n_tests_that_only_flake_once,
        n_tests_that_flake_more_than_once):

    print(f'\nReport at the most granular test level')
    print(f'\nThe CTS has {n_tests} tests in total')
    print(f'\nThere are {n_flakes} flaky tests across {n_runs} runs of the CTS')
    print(f'\nThis is {n_flakes/n_tests}% of the total CTS tests')
    print(f'\nOf these flaky tests, {n_tests_that_only_flake_once} only had one flake')
    print('(i.e. one run in which their result differed from the result in all the other runs),')
    print(f'while {n_tests_that_flake_more_than_once} flaked more than once.')
    print('\n')

def analyse(flaky_df, n_runs, n_tests):

    n_flakes = len(flaky_df)
    print(f'There are {n_flakes} flaky tests')
    if n_flakes == 0:
        exit()

    # Get distribution of passes and fails
    flaky_df['n_pass'] = flaky_df.filter(regex='result_*').apply(count_pass, axis=1)
    flaky_df['n_fail'] = flaky_df.filter(regex='result_*').apply(count_fail, axis=1)

    passes = flaky_df['n_pass'].value_counts()
    fails = flaky_df['n_fail'].value_counts()

    assert ((passes[1] + passes[n_runs - 1]) == (fails[1] + fails[n_runs - 1]))

    n_tests_that_only_flake_once = passes[1] + passes[n_runs - 1]
    n_tests_that_flake_more_than_once = n_flakes - n_tests_that_only_flake_once

    # Report results
    report_results(n_flakes, n_runs, n_tests, n_tests_that_only_flake_once, n_tests_that_flake_more_than_once)

if __name__=="__main__":
    main()