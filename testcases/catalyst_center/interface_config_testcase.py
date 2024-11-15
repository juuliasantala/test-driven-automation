#!/usr/bin/env python
'''
Configuration validation ("Is it there?") to test port status by
executing a simple Catalyst Center API test.

Copyright (c) 2024 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
'''

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
__author__ = "Juulia Santala"
__email__ = "jusantal@cisco.com"

from pyats import aetest
from dnacentersdk import api 

class CommonSetup(aetest.CommonSetup):
    '''
    Common setup tasks - this class is instantiated only once per testscript.
    '''
    @aetest.subsection
    def mark_tests_for_looping(self, device_list):
        """
        device_list includes details (name and uuid) for each of the devices
        whose interface configuration is to be tested.
        This method loops through all the devices in the device_list and calls
        the test InterfaceConfigTestcase on all of them one by one.
        """
        aetest.loop.mark(InterfaceConfigTestcase, device=device_list)

class InterfaceConfigTestcase(aetest.Testcase):
    '''
    Simple Testcase for checking port status using Cisco Catalyst Center.
    '''

    @aetest.setup
    def get_device_interface_details(self, steps, device, interfaces, cat_creds):
        '''
        Retrieve interface configuration from Catalyst Center for the selected device
        '''

        with  steps.start(
            f" Retrieving interface details for: {device}",
            continue_=True
        ) as step:
            try:

                catalyst_center = api.DNACenterAPI(
                    base_url=f"https://{cat_creds['url']}",
                    username=cat_creds['username'],
                    password=cat_creds['password'],
                    verify=False
                )
                interfaces = catalyst_center.devices.poe_interface_details(device_uuid=device,
                                                                           interface_name_list=interfaces)
                self.interfaces = interfaces["response"]

            except Exception as err:
                step.failed(err)

            else:
                step.passed()


    @aetest.test
    def test_interface_status(self, steps, device):
        '''
        Test the retrieved interface status against the expected result.
        '''

        for interface in self.interfaces:
            interface_name = interface["interfaceName"]
            interface_oper_status = interface["operStatus"]

            with steps.start(
                f"{device}: {interface_name}",
                description=f"Checking {device}: {interface_name}",
                continue_=True
            ) as step:

                try:
                    assert interface_oper_status == "ON"

                except:
                    step.failed(f"{device}: {interface_name} is ❌ DOWN ❌")

                else:
                    step.passed(f"{device}: {interface_name} is ✅ UP ✅")

    @aetest.cleanup
    def cleanup(self):
        ''' No cleanup needed for this Catalyst Center testcase '''
        pass

if __name__ == "__main__":
    import os

    # define your Catalyst Center details
    cat_creds = {
        "url": os.getenv("DNAC_HOST") or "sandboxdnac.cisco.com",
        "username": os.getenv("DNAC_USERNAME") or "devnetuser",
        "password": os.getenv("DNAC_PASSWORD") or "Cisco123!"
    }

    # define your devices as a tuple or a list using the "uuid" of the network device
    devices = ("a29650a1-bca7-4913-8b02-7474f0e8215c", "85ce77aa-3627-4d69-99ea-085d700cbd0f", "f2ee94ae-c1f7-4114-9a00-a4348240204f")
    # devices = os.getenv("DNAC_CATALYST_IDS").split(",")

    # define the interfaces to be targeted in one string, separated by commas
    interfaces="GigabitEthernet1/0/1,GigabitEthernet1/0/2,GigabitEthernet1/0/3"

    # Call the test with the defined device_list, interfaces, and credentials
    aetest.main(device_list=devices, interfaces=interfaces, cat_creds=cat_creds)
