# Test Datasets

This directory contains test datasets for the bulk upload workflow test runner.

## Directory Structure

```
datasets/
├── acme/
│   ├── small_ok.zip          # Valid small dataset (synthetic)
│   └── small_bad_header.zip  # Invalid header dataset (synthetic)
├── beta/
│   └── medium_ok.zip         # Valid medium dataset (sanitized)
└── README.md                 # This file
```

## Dataset Classifications

### Synthetic
Completely artificial data generated for testing purposes. Contains no real user information.
Examples: `acme_small_ok`, `acme_small_bad_header`

### Sanitized
Real data that has been anonymized and sanitized to remove all PII and sensitive information.
Example: `beta_medium_ok`

### Real-Sensitive
Real production data that may contain sensitive information. These datasets should:
- Only be used in secure, authorized environments
- Never be committed to version control
- Only be included in test runs when explicitly enabled with `--include-sensitive` flag

## Creating Test Datasets

### For Synthetic Datasets

1. Create a CSV or data file with the expected schema
2. Add intentional errors if testing error handling (e.g., bad headers, invalid values)
3. Zip the file
4. Place in appropriate subdirectory
5. Add entry to `catalog.yml` with `classification: synthetic`

### For Sanitized Datasets

1. Start with a real dataset
2. Remove all PII:
   - Replace names with random generated names
   - Replace emails with fake emails
   - Replace phone numbers, addresses, etc.
3. Validate that no sensitive data remains
4. Zip the file
5. Place in appropriate subdirectory
6. Add entry to `catalog.yml` with `classification: sanitized`

### For Real-Sensitive Datasets

1. Obtain proper authorization
2. Ensure data is stored securely
3. Add to `.gitignore` to prevent accidental commits
4. Add entry to `catalog.yml` with `classification: real-sensitive`
5. Document security requirements

## Sample Dataset Specifications

### acme_small_ok.zip
- **Type:** CSV
- **Rows:** ~100
- **Columns:** id, name, email, value
- **Expected:** Success

### acme_small_bad_header.zip
- **Type:** CSV  - **Rows:** ~50
- **Issue:** Missing required column 'id'
- **Expected:** Input error

### beta_medium_ok.zip
- **Type:** CSV
- **Rows:** ~1000
- **Columns:** id, timestamp, metric, value
- **Expected:** Success

## Adding New Datasets

1. Create the dataset file
2. Zip it (if required by your application)
3. Place in appropriate subdirectory
4. Add entry to `catalog.yml`:

```yaml
datasets:
  - id: my_new_dataset
    path: datasets/my_org/my_file.zip
    classification: synthetic  # or sanitized, real-sensitive
    expected: success  # or input_error
```

5. Run tests to verify

## Security Notes

- **Never commit real-sensitive datasets** to version control
- Keep sensitive data encrypted at rest
- Use secure file transfer methods
- Limit access to authorized personnel only
- Audit dataset access regularly

## Placeholder Files

**Note:** The `.zip` files in this directory are placeholders. Replace them with actual test datasets that match your application's expected format before running tests.

To create placeholder files for testing the runner itself:

```bash
# Create placeholder CSV files
echo "id,name,email,value" > acme_small_ok.csv
echo "1,Test User,test@example.com,100" >> acme_small_ok.csv
zip datasets/acme/small_ok.zip acme_small_ok.csv

echo "name,email,value" > acme_small_bad.csv  # Missing 'id' column
echo "Test User,test@example.com,100" >> acme_small_bad.csv
zip datasets/acme/small_bad_header.zip acme_small_bad.csv

echo "id,timestamp,metric,value" > beta_medium_ok.csv
for i in {1..1000}; do
  echo "$i,2024-01-01T00:00:00Z,metric_$i,$((RANDOM % 1000))" >> beta_medium_ok.csv
done
zip datasets/beta/medium_ok.zip beta_medium_ok.csv

# Clean up CSV files
rm *.csv
```
