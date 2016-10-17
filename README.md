# Caracalla


### What is caracalla?
Currently caracalla houses utilities to performance test candlepin/server.

### How to run tests?

 * bind.jmx
   * This test is a basic test that allows to measure performance of multoiple consumers binding against one pool.
   * Steps:
     * Deploy candlepin server ( ./server/bin/deploy -gat )
     * Select a pool generated from the above step and ensure it has a quantity of atleast 100
     * Open the jmx file in jmeter 3.0(+)
     * Select the node marked Entitlement creation and ovveride the variables to point to your local candlepin
     * For the first run only, enable the node marked "setUp Thread Group - Run Once". This will create consumers and populate the input file required for the next steps
     * run the jmeter test and observe the results.
 * candlepin-throughput.jmx
   * This test measures throughput of various candlepin REST APIs based on specified throughput ratios.
   * Tweak this file only through the jmeter GUI. There are a lot of variables to tweak in the "Configuration" section, special ones to note are the Environment Config and Authorization variable in HTTP Header Manager.
   * tweak candlepin-throughput.prop as needed
   * generate following input files in the folder specified in the above file:
     * consumers_uuid_certs_ser.csv : consumer uuid
     * consumers_uuid.csv : consumer uuid
     * consumer_uuids-serials.csv : consumer_uuid, serials
     * get_owners_ownerkey_consumers.csv : ownerkey
     * hypervisors.csv : ownerkey, numVirtHosts, numVirtGuests
     * owners_account.csv : ownerkey
     * owners_account_info.csv : ownerkey
     * owners_account_pools.csv : ownerkey
     * owners_account_subs.csv : ownerkey
     * pools_owner_id.csv : owner id
     * post_consumers_uuid_entitlements.csv : ownerkey, poolid, sku, totalAvailable, expires
    * execute the test via GUI or cli:
      * apache-jmeter-3.0/bin/jmeter -n -t candlepin-throughput.jmx  -p candlepin-throughput.prop

