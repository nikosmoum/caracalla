## Required setup

The script assumes the following set up is available:

 * A hypervisor with a vm snapshotted with the name "readyfortestsnap" for running candlepin and jmeter with:
   * A user "jenkins" that can sudo without a password required
   * Candlepin installed with tomcat and mysql service enabled. ( local mysql is required initially for deploy )
   * Apache jmeter installed in /opt
 * A hypervisor with a vm snapshotted with the name "readyfortestsnap" for running mysql with:
   * Mysql service installed and enabled
   * Candlepin database imported, and should be remotely accessible from the above vm using username candlepin and no password

Note:
 * **Running this test will shutdown all vms on the hypervisors used in the setup**

Example inventory:

```yaml
[performance-hypervisors:children]
performance-candlepin-hypervisor
performance-database-hypervisor

[performance-candlepin-hypervisor]
candlepin-hypervisor.mycompany.com

[performance-candlepin-hypervisor:vars]
ansible_user=root
perf_vm_domain=CP

[performance-database-hypervisor]
database-hypervisor.mycompany.com

[performance-database-hypervisor:vars]
ansible_user=root
perf_vm_domain=candlepin-perf

[performance-candlepin-vm]
candlepin-vm.mycompany.com mysql_vm_hostname=database-vm.mycompany.com

[localhost]
127.0.0.1 performance_vm_hostnames='["candlepin-vm.mycompany.com", "database-vm.mycompany.com"]' connection=local
```
