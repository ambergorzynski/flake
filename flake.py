import pandas as pd
from pathlib import Path

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
    
def main():
    base = Path('/data/dev/flake')
    flaky_csv = Path(base,'data/cts_results/clean_090525/clean_flaky_tests.csv')
    all_csv = Path(base,'data/cts_results/clean_090525/all_results.csv')
    n_runs = 10

    flaky_df = pd.read_csv(flaky_csv, sep='\t')
    all_df = pd.read_csv(all_csv, sep='\t')
    all_tests = all_df['test'].to_list()
    n_tests = len(all_tests)

    # Analyse results at most granular level (test x parameters)
    analyse(flaky_df, n_runs, n_tests)

    # Analyse results at the test level (not parameterised)
    tests = flaky_df['test'].to_list()
    non_parameterised_tests = set([':'.join(x.split(':')[:3]) for x in tests])
    non_parameterised_tests_all = set([':'.join(x.split(':')[:3]) for x in all_tests])

    print(f'The number of unique flaky non-parameterised tests is: {len(non_parameterised_tests)}')
    print(f'This is {len(non_parameterised_tests)/len(non_parameterised_tests_all)}% of all non-parameterised tests')

    # Analyse results at the test group level (file)
    test_groups = set([''.join(x.split(':')[:2]) for x in non_parameterised_tests])
    test_groups_all = set([''.join(x.split(':')[:2]) for x in non_parameterised_tests_all])
    print(f'The number of unique flaky test groups is: {len(test_groups)}')
    print(f'This is {len(test_groups)/len(test_groups_all)}% of all test groups')

if __name__=="__main__":
    main()