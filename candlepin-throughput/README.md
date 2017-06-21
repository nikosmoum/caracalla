## Notes
   * This test measures throughput of various candlepin REST APIs based on specified throughput ratios.
   * Tweak the jmeter file only through the jmeter GUI. There are a lot of variables to tweak
     in the "Configuration" section, special ones to note are the Environment Config and
     Authorization variable in HTTP Header Manager.
   * Generate the csv files needed for this test using the command:
      * ```./generate-csv.py candlepin-throughput/csv_config.json```
   * Tweak candlepin-throughput.prop as needed, at the very least provide the location of the csv files above.
   * Execute the test via GUI or cli:
      * ```apache-jmeter-3.0/bin/jmeter -n -t candlepin-throughput.jmx  -p candlepin-throughput.prop```

