# Test flakiness
- Conformance Test Suites are used to ensure that implementations adhere to specifications
- **Test flakiness** refers to the unpredictable behaviour of some tests, whereby they non-deterministically fail despite no change in the code
- Flakiness is a problem because it means that a passing test cannot be trusted to assure conformance; neither can a failing test be trusted to signal non-conformance
- The scripts here explore flakiness within the WebGPU CTS in the following ways:
    - Under what conditions does flaking occur? E.g. running the full CTS vs running individual tests
    - Which tests are flaky? What proportion of the overall test suite does this constitute?
    - What are the characteristics of the flaky tests?
    - How many times does a test need to be run to be confident of the 'correct' result?

## Run analysis of WebGPU CTS flakiness

# Run the CTS multiple times
Update the relevant filepaths in `run_cts.py`
```
python run_cts.py
```

# Analyse the results
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python analyse_flake.py $PATH_TO_OUTPUT_FOLDER $NUMBER_OF_CTS_RUNS
```