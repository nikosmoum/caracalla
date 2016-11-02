# Caracalla


### What is caracalla?
Currently caracalla houses utilities to performance test candlepin/server.

### How to run tests?

 * bind.jmx
   * This test is a basic test that allows to measure performance of multiple consumers binding against one pool.
   * Steps:
     * Deploy candlepin server ( ./server/bin/deploy -gat )
     * Select a pool generated from the above step and ensure it has a quantity of atleast 100
     * Open the jmx file in jmeter 3.0(+)
     * Select the node marked Entitlement creation and ovveride the variables to point to your local candlepin
     * Consumers are created only once , if you wish to create consumers again , then please change the value of the User Defined Variable "ForceCreateConsumerFile"  to true
