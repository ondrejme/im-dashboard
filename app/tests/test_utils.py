#! /usr/bin/env python
#
# IM - Infrastructure Manager
# Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from app import utils
from mock import patch, MagicMock


class TestUtils(unittest.TestCase):
    """Class to test the Utils functions."""

    def test_getUserVOs(self):
        entitlements = ['urn:mace:egi.eu:group:vo.test.egi.eu:role=member#aai.egi.eu',
                        'urn:mace:egi.eu:group:vo.test2.egi.eu:role=member#aai.egi.eu']
        res = utils.getUserVOs(entitlements)
        self.assertEquals(res, ['vo.test.egi.eu', 'vo.test2.egi.eu'])

    @patch("app.utils.getCachedProjectIDs")
    @patch("app.utils.getCachedSiteList")
    @patch("app.utils._getStaticSitesInfo")
    def test_getUserAuthData(self, getStaticSitesInfo, getCachedSiteList, getCachedProjectIDs):
        cred = MagicMock()
        cred.get_cred.return_value = {"project": "project_name"}
        getCachedSiteList.return_value = {
            'CESGA': {'url': 'https://fedcloud-osservices.egi.cesga.es:5000', 'state': '', 'id': '11548G0'},
            'IFCA': {'url': 'https://api.cloud.ifca.es:5000', 'state': '', 'id': 'ifca'}
        }
        getStaticSitesInfo.return_value = [{"name": "static_site_name", "api_version": "1.1"}]
        getCachedProjectIDs.return_value = {"vo_name_st": "project_id_st", "vo_name": "project_id"}

        res = utils.getUserAuthData("token", cred, "user")
        self.assertEquals(res, ("type = InfrastructureManager; token = token\\nid = ost1; type = OpenStack;"
                                " username = egi.eu; tenant = openid; auth_version = 3.x_oidc_access_token;"
                                " host = https://fedcloud-osservices.egi.cesga.es:5000; password = 'token';"
                                " domain = project_name\\nid = ost2; type = OpenStack; username = egi.eu;"
                                " tenant = openid; auth_version = 3.x_oidc_access_token; host ="
                                " https://api.cloud.ifca.es:5000; password = 'token'; domain = project_name"))

        res = utils.getUserAuthData("token", cred, "user", "vo_name", "CESGA")
        self.assertEquals(res, ("type = InfrastructureManager; token = token\\nid = ost1; type = OpenStack;"
                                " username = egi.eu; tenant = openid; auth_version = 3.x_oidc_access_token;"
                                " host = https://fedcloud-osservices.egi.cesga.es:5000; password = 'token';"
                                " domain = project_id"))
        self.assertEqual(cred.write_creds.call_args_list[0][0], ('CESGA', 'user', {'project': 'project_id'}))

    @patch("app.utils.getCachedSiteList")
    @patch('libcloud.compute.drivers.openstack.OpenStackNodeDriver')
    def test_get_site_images(self, get_driver, getCachedSiteList):
        cred = MagicMock()
        cred.get_cred.return_value = {"project": "project_name"}
        getCachedSiteList.return_value = {'CESGA': {'url': 'https://fedcloud-osservices.egi.cesga.es:5000',
                                          'state': '', 'id': '11548G0'}}
        driver = MagicMock()
        get_driver.return_value = driver
        image1 = MagicMock()
        image1.id = "imageid1"
        image1.name = "imagename1"
        driver.list_images.return_value = [image1]
        res = utils.get_site_images("CESGA", "vo.access.egi.eu", "token", cred, "user")
        self.assertEquals(res, [('imagename1', 'imageid1')])

    @patch("app.utils.getCachedSiteList")
    @patch('libcloud.compute.drivers.openstack.OpenStackNodeDriver')
    def test_get_site_usage(self, get_driver, getCachedSiteList):
        cred = MagicMock()
        cred.get_cred.return_value = {"project": "project_name"}
        getCachedSiteList.return_value = {'CESGA': {'url': 'https://fedcloud-osservices.egi.cesga.es:5000',
                                          'state': '', 'id': '11548G0'}}
        driver = MagicMock()
        get_driver.return_value = driver
        quotas = MagicMock()
        quotas.cores.in_use = 1
        quotas.cores.reserved = 0
        quotas.cores.limit = 10
        quotas.ram.in_use = 10240
        quotas.ram.reserved = 0
        quotas.ram.limit = 102400
        quotas.instances.in_use = 1
        quotas.instances.reserved = 0
        quotas.instances.limit = 10
        quotas.floating_ips.in_use = 1
        quotas.floating_ips.reserved = 0
        quotas.floating_ips.limit = 10
        quotas.security_groups.in_use = 1
        quotas.security_groups.reserved = 0
        quotas.security_groups.limit = 10
        driver.ex_get_quota_set.return_value = quotas
        net_quotas = MagicMock()
        net_quotas.floatingip.in_use = 2
        net_quotas.floatingip.reserved = 0
        net_quotas.floatingip.limit = 4
        net_quotas.security_group.in_use = 2
        net_quotas.security_group.reserved = 0
        net_quotas.security_group.limit = 10
        driver.ex_get_network_quotas.return_value = net_quotas
        res = utils.get_site_usage("CESGA", "vo.access.egi.eu", "token", cred, "user")
        quotas_dict = {}
        quotas_dict["cores"] = {"used": 1, "limit": 10}
        quotas_dict["ram"] = {"used": 10, "limit": 100}
        quotas_dict["instances"] = {"used": 1, "limit": 10}
        quotas_dict["floating_ips"] = {"used": 2, "limit": 4}
        quotas_dict["security_groups"] = {"used": 2, "limit": 10}
        self.assertEquals(res, quotas_dict)


if __name__ == '__main__':
    unittest.main()
