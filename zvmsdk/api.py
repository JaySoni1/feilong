#  Copyright Contributors to the Feilong Project.
#  SPDX-License-Identifier: Apache-2.0

# Copyright 2017,2023 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import netaddr
import six
import ast

from zvmsdk import config
from zvmsdk import constants
from zvmsdk import exception
from zvmsdk import hostops
from zvmsdk import imageops
from zvmsdk import log
from zvmsdk import monitor
from zvmsdk import networkops
from zvmsdk import vmops
from zvmsdk import smtclient
from zvmsdk import volumeop
from zvmsdk import database
from zvmsdk import utils as zvmutils


CONF = config.CONF
LOG = log.LOG


def check_guest_exist(check_index=0):
    """Check guest exist in database.

    :param check_index: The parameter index of userid(s), default as 0

    """

    def outer(f):
        @six.wraps(f)
        def inner(self, *args, **kw):
            userids = args[check_index]

            if isinstance(userids, list):
                # convert all userids to upper case
                userids = [uid.upper() for uid in userids]
                new_args = (args[:check_index] + (userids,) +
                            args[check_index + 1:])
            else:
                # convert the userid to upper case
                userids = userids.upper()
                new_args = (args[:check_index] + (userids,) +
                            args[check_index + 1:])
                userids = [userids]

            self._vmops.check_guests_exist_in_db(userids)

            return f(self, *new_args, **kw)
        return inner
    return outer


def check_fcp_exist(check_index=0):
    """Check FCP exist in database.

    :param check_index: The parameter index of fcp, default as 0

    """

    def outer(f):
        @six.wraps(f)
        def inner(self, *args, **kw):
            fcp = args[check_index]

            self._volumeop.check_fcp_exist_in_db(fcp)

            return f(self, *args, **kw)
        return inner
    return outer


class SDKAPI(object):
    """Compute action interfaces."""

    def __init__(self, **kwargs):
        self._vmops = vmops.get_vmops()
        self._smtclient = smtclient.get_smtclient()
        self._hostops = hostops.get_hostops()
        self._networkops = networkops.get_networkops()
        self._imageops = imageops.get_imageops()
        self._monitor = monitor.get_monitor()
        self._volumeop = volumeop.get_volumeop()
        self._GuestDbOperator = database.GuestDbOperator()
        self._NetworkDbOperator = database.NetworkDbOperator()

    @check_guest_exist()
    def guest_start(self, userid, timeout=0):
        """Power on a virtual machine.

        :param str userid: the id of the virtual machine to be power on
        :param int timeout: the timeout of waiting virtual machine reachable
                            default as 0, which mean not wait for virtual
                            machine reachable status

        :returns: None
        """
        action = "start guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_start(userid, timeout)

    @check_guest_exist()
    def guest_stop(self, userid, **kwargs):
        """Power off a virtual machine.

        :param str userid: the id of the virtual machine to be power off
        :param dict kwargs:
               - timeout=<value>:
                 Integer, time to wait for vm to be deactivate, the
                 recommended value is 300
               - poll_interval=<value>
                 Integer, how often to signal guest while waiting for it
                 to be deactivate, the recommended value is 20

        :returns: None
        """

        action = "stop guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_stop(userid, **kwargs)

    @check_guest_exist()
    def guest_softstop(self, userid, **kwargs):
        """Issue a shutdown command to shutdown the OS in a virtual
        machine and then log the virtual machine off z/VM..

        :param str userid: the id of the virtual machine to be power off
        :param dict kwargs:
               - timeout=<value>:
                 Integer, time to wait for vm to be deactivate, the
                 recommended value is 300
               - poll_interval=<value>
                 Integer, how often to signal guest while waiting for it
                 to be deactivate, the recommended value is 20

        :returns: None
        """

        action = "soft stop guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_softstop(userid, **kwargs)

    @check_guest_exist()
    def guest_reboot(self, userid):
        """Reboot a virtual machine
        :param str userid: the id of the virtual machine to be reboot
        :returns: None
        """
        action = "reboot guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_reboot(userid)

    @check_guest_exist()
    def guest_reset(self, userid):
        """reset a virtual machine
        :param str userid: the id of the virtual machine to be reset
        :returns: None
        """
        action = "reset guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_reset(userid)

    @check_guest_exist()
    def guest_pause(self, userid):
        """Pause a virtual machine.

        :param str userid: the id of the virtual machine to be paused
        :returns: None
        """
        action = "pause guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_pause(userid)

    @check_guest_exist()
    def guest_unpause(self, userid):
        """Unpause a virtual machine.

        :param str userid: the id of the virtual machine to be unpaused
        :returns: None
        """
        action = "unpause guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_unpause(userid)

    @check_guest_exist()
    def guest_get_power_state(self, userid):
        """Returns power state."""
        if not zvmutils.check_userid_exist(userid.upper()):
            LOG.error("User directory of '%s' does not exist "
                      "although it is in DB. The guest could have been "
                      "deleted out of z/VM Cloud Connector." % userid)
            raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % userid), modID='guest', rs=3)
        action = "get power state of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_power_state(userid)

    @check_guest_exist()
    def guest_get_info(self, userid):
        """Get the status of a virtual machine.

        :param str userid: the id of the virtual machine

        :returns: Dictionary contains:
                  power_state: (str) the running state, one of on | off
                  max_mem_kb: (int) the maximum memory in KBytes allowed
                  mem_kb: (int) the memory in KBytes used by the instance
                  num_cpu: (int) the number of virtual CPUs for the instance
                  cpu_time_us: (int) the CPU time used in microseconds
        """
        action = "get info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_info(userid)

    def guest_get_power_state_real(self, userid):
        """Returns power state of a virtual machine from hypervisor."""
        action = "get power state of guest '%s' from hypervisor" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_power_state(userid)

    def guest_get_adapters_info(self, userid):
        """Get the network information of a virtual machine.
        this userid may not in zCC.

        :param str userid: the id of the virtual machine

        :returns: Dictionary contains:
                  ip: (str) the IP address of the virtual machine
                  mac: (str) the MAC address of the virtual machine
        """
        action = "get network info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_adapters_info(userid)

    def guest_get_disks_info(self, userid):
        """Get the disks information of a virtual machine.

        :param str userid: the id of the virtual machine

        :returns: Dictionary contains:
                TODO
        """
        action = "get disks info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_disks_info(userid)

    def guest_get_user_direct(self, userid):
        """Get user direct of the specified guest vm

        :param str userid: the user id of the guest vm
        :returns: Dictionary describing user direct and check info result
        :rtype: dict
        """
        action = "get the user direct of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            inst_info = self._vmops.get_definition_info(userid)
            user_direct = inst_info['user_direct']
            item = -1
            new_info = ""
            for info in user_direct:
                item += 1
                # replace password with ******
                if info.startswith('USER') or info.startswith('IDENTITY'):
                    fields = info.split()
                    for i in range(len(fields)):
                        if i != 2:
                            new_info += (fields[i] + ' ')
                        else:
                            new_info += ('******' + ' ')
                    user_direct[item] = new_info
                    break
            inst_info['user_direct'] = user_direct
            return inst_info

    def guest_list(self):
        """list names of all the VMs on this host.

        :returns: names of the vm on this host, in a list.
        """
        action = "list guests on host"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.guest_list()

    def host_get_info(self):
        """ Retrieve host information including host, memory, disk etc.

        :returns: Dictionary describing resources
        """
        action = "get host information"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.get_info()

    def host_get_diskpool_volumes(self, disk_pool=None):
        """ Retrieve diskpool volumes.
        :param str disk_pool: the disk pool info. It use ':' to separate
        disk pool type and pool name, eg "ECKD:eckdpool" or "FBA:fbapool"
        :returns: Dictionary describing disk pool usage info
        """
        # disk_pool is optional. disk_pool default to None because
        # it is more convenient for users to just type function name when
        # they want to get the disk pool info of CONF.zvm.disk_pool.
        # The default value of CONF.zvm.disk_pool is None, if it's configured,
        # the format must be "ECKD:eckdpool" or "FBA:fbapool".
        disk_pool = disk_pool
        if disk_pool is None:
            disk_pool = CONF.zvm.disk_pool
            if disk_pool is not None:
                disk_pools = disk_pool.split(",")
                if len(disk_pools) == 1:
                    disk_pool = disk_pools[0]
                else:
                    errmsg = ("disk_pool input is required if multiple disk_pool"
                              " is configured for sdkserver.")
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
        if disk_pool is None:
            # Support disk_pool not configured, return empty list
            return {}
        if ':' not in disk_pool:
            msg = ('Invalid input parameter disk_pool, expect ":" in'
                   'disk_pool, eg. ECKD:eckdpool')
            LOG.error(msg)
            raise exception.SDKInvalidInputFormat(msg)
        diskpool_type = disk_pool.split(':')[0].upper()
        if diskpool_type not in ('ECKD', 'FBA'):
            msg = ('Invalid disk pool type found in disk_pool, expect'
                   'disk_pool like ECKD:eckdpool or FBA:fbapool')
            LOG.error(msg)
            raise exception.SDKInvalidInputFormat(msg)

        action = "get the volumes of disk pool: '%s'" % disk_pool
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.diskpool_get_volumes(disk_pool)

    def host_get_volume_info(self, volume=None):
        """ Retrieve volume information.
        :param str volume: the volume name to identify the DASD device.
        It's 1 to 6 hexadecimal characters.
        :returns: Dictionary describing the volume description info
        """
        volume_name = volume
        if volume_name is None:
            errmsg = ("Invalid volume input None, volume must be specified.")
            LOG.error(errmsg)
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        action = "get information of the volume: '%s'" % volume_name
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.get_volume_info(volume_name.upper())

    def host_get_guest_list(self):
        """list names of all the VMs on the host.
        :returns: names of the vm on this hypervisor, in a list.
        """
        action = "list guests on the host"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._hostops.guest_list()

    def host_diskpool_get_info(self, disk_pool=None, details=False):
        """ Retrieve diskpool information.
        :param str disk_pool: the disk pool info. It use ':' to separate
        disk pool type and pool name, eg "ECKD:eckdpool" or "FBA:fbapool"
        :param boolean details: if it's True, get the free space
        of the volumes among the diskpool.
        :returns: if details is False, Dictionary describing disk pool usage info,
        if details is True, Dictionary describing the free space of the volumes
        among the diskpool.

        disk_pool is optional. disk_pool default to None because
        it is more convenient for users to just type function name when
        they want to get the disk pool info of CONF.zvm.disk_pool.
        The default value of CONF.zvm.disk_pool is None, if it's configured,
        the format must be "ECKD:eckdpool" or "FBA:fbapool".
        details is optional. details default to False.
        1.example if details is False:
        {'disk_total': 2034, 'disk_used': 1469, 'disk_available': 564}
        2. example if details is True:
        {
             'poolname': [
                 {'volume_name': 'vol1',
                  'device_type': 'type1',
                  'start_cylinder': '100',
                  'free_size': '1456',
                  'dasd_group': 'poolname',
                  'region_name': 'vol1'
                 },
                 {'volume_name': 'vol2',
                  'device_type': 'typ1',
                  'start_cylinder': '3000',
                  'free_size': '15291',
                  'dasd_group': 'poolname',
                  'region_name': 'vol2'
                 },
             ]
        }
        """
        disk_pool = disk_pool or CONF.zvm.disk_pool
        if disk_pool is None:
            if not details:
                # Return 0 directly if disk_pool not configured
                return {'disk_total': 0, 'disk_used': 0, 'disk_available': 0}
            else:
                return {}
        disk_pools_total = 0
        disk_pools_used = 0
        disk_pools_available = 0
        disk_pools = disk_pool.split(',')
        disk_pool_info = {}
        for disk_pool in disk_pools:
            if ':' not in disk_pool:
                msg = ('Invalid input parameter disk_pool, expect ":" in'
                       'disk_pool, eg. ECKD:eckdpool')
                LOG.error(msg)
                raise exception.SDKInvalidInputFormat(msg)
            diskpool_type = disk_pool.split(':')[0].upper()
            diskpool_name = disk_pool.split(':')[1]
            if diskpool_type not in ('ECKD', 'FBA'):
                msg = ('Invalid disk pool type found in disk_pool, expect'
                       'disk_pool like ECKD:eckdpool or FBA:fbapool')
                LOG.error(msg)
                raise exception.SDKInvalidInputFormat(msg)

            action = "get information of disk pool: '%s' '%s'" % (disk_pool, details)
            with zvmutils.log_and_reraise_sdkbase_error(action):
                dp_info = self._hostops.diskpool_get_info(diskpool_name, details)
                if not details:
                    disk_pools_total = disk_pools_total + dp_info.get("disk_total", 0)
                    disk_pools_used = disk_pools_used + dp_info.get("disk_used", 0)
                    disk_pools_available = disk_pools_available + dp_info.get("disk_available", 0)
                    disk_pool_info = {
                        'disk_total': disk_pools_total,
                        'disk_used': disk_pools_used,
                        'disk_available': disk_pools_available
                    }
                else:
                    disk_pool_info.update(dp_info)
        return disk_pool_info

    def image_delete(self, image_name):
        """Delete image from image repository

        :param image_name: the name of the image to be deleted
        """
        try:
            self._imageops.image_delete(image_name)
        except exception.SDKBaseException:
            LOG.error("Failed to delete image '%s'" % image_name)
            raise

    def image_get_root_disk_size(self, image_name):
        """Get the root disk size of the image

        :param image_name: the image name in image Repository
        :returns: the disk size in units CYL or BLK
        """
        try:
            return self._imageops.image_get_root_disk_size(image_name)
        except exception.SDKBaseException:
            LOG.error("Failed to get root disk size units of image '%s'" %
                      image_name)
            raise

    def image_import(self, image_name, url, image_meta, remote_host=None):
        """Import image to zvmsdk image repository

        :param image_name: image name that can be uniquely identify an image
        :param str url: image url to specify the location of image such as
               http://netloc/path/to/file.tar.gz.0
               https://netloc/path/to/file.tar.gz.0
               file:///path/to/file.tar.gz.0
        :param dict image_meta:
               a dictionary to describe the image info, such as md5sum,
               os_version. For example:
               {'os_version': 'rhel6.2',
               'md5sum': ' 46f199c336eab1e35a72fa6b5f6f11f5',
               'disk_type': 'DASD'}
        :param string remote_host:
                if the image url schema is file, the remote_host is used to
                indicate where the image comes from, the format is username@IP
                eg. nova@192.168.99.1, the default value is None, it indicate
                the image is from a local file system. If the image url schema
                is http/https, this value will be useless
        """
        try:
            self._imageops.image_import(image_name, url, image_meta,
                                        remote_host=remote_host)
        except exception.SDKBaseException:
            LOG.error("Failed to import image '%s'" % image_name)
            raise

    def image_query(self, imagename=None):
        """Get the list of image info in image repository

        :param imagename:  Used to retrieve the specified image info,
               if not specified, all images info will be returned

        :returns: A list that contains the specified or all images info
        """
        try:
            return self._imageops.image_query(imagename)
        except exception.SDKBaseException:
            LOG.error("Failed to query image")
            raise

    def image_export(self, image_name, dest_url, remote_host=None):
        """Export the image to the specified location
        :param image_name: image name that can be uniquely identify an image
        :param dest_url: the location of exported image, eg.
        file:///opt/images/export.img, now only support export to remote server
        or local server's file system
        :param remote_host: the server that the image will be export to, if
        remote_host is None, the image will be stored in the dest_path in
        local server,  the format is username@IP eg. nova@9.x.x.x
        :returns a dictionary that contains the exported image info
        {
        'image_name': the image_name that exported
        'image_path': the image_path after exported
        'os_version': the os version of the exported image
        'md5sum': the md5sum of the original image
        'comments': the comments of the original image
        }
        """
        try:
            return self._imageops.image_export(image_name, dest_url,
                                               remote_host)
        except exception.SDKBaseException:
            LOG.error("Failed to export image '%s'" % image_name)
            raise

    @check_guest_exist()
    def guest_deploy(self, userid, image_name, transportfiles=None,
                     remotehost=None, vdev=None, hostname=None,
                     skipdiskcopy=False):
        """ Deploy the image to vm.

        :param userid: (str) the user id of the vm
        :param image_name: (str) If the skipdiskcopy is False, this would be
               used as the name of image that used to deploy the vm;
               Otherwise, this value should be the os version.
        :param transportfiles: (str) the files that used to customize the vm
        :param remotehost: the server where the transportfiles located, the
               format is username@IP, eg nova@192.168.99.1
        :param vdev: (str) the device that image will be deploy to
        :param hostname: (str) the hostname of the vm. This parameter will be
               ignored if transportfiles present.
        :param skipdiskcopy: (bool) whether to skip the disk copy process.
               If True, the os version should be specified in the parameter
               image_name.
        """
        action = ("deploy image '%(img)s' to guest '%(vm)s'" %
                  {'img': image_name, 'vm': userid})
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_deploy(userid, image_name, transportfiles,
                                     remotehost, vdev, hostname, skipdiskcopy)

    @check_guest_exist()
    def guest_capture(self, userid, image_name, capture_type='rootonly',
                      compress_level=6):
        """ Capture the guest to generate a image

        :param userid: (str) the user id of the vm
        :param image_name: (str) the unique image name after capture
        :param capture_type: (str) the type of capture, the value can be:
               rootonly: indicate just root device will be captured
               alldisks: indicate all the devices of the userid will be
               captured
        :param compress_level: the compression level of the image, default
               is 6
        """
        action = ("capture guest '%(vm)s' to generate image '%(img)s'" %
                  {'vm': userid, 'img': image_name})
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_capture(userid, image_name,
                                      capture_type=capture_type,
                                      compress_level=compress_level)

    @check_guest_exist()
    def guest_create_nic(self, userid, vdev=None, nic_id=None,
                         mac_addr=None, active=False):
        """ Create the nic for the vm, add NICDEF record into the user direct.

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param str nic_id: nic identifier
        :param str mac_addr: mac address, it is only be used when changing
               the guest's user direct. Format should be xx:xx:xx:xx:xx:xx,
               and x is a hexadecimal digit
        :param bool active: whether add a nic on active guest system

        :returns: nic device number, 1- to 4- hexadecimal digits
        :rtype: str
        """
        if mac_addr is not None:
            if not zvmutils.valid_mac_addr(mac_addr):
                raise exception.SDKInvalidInputFormat(
                    msg=("Invalid mac address, format should be "
                         "xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit"))
        return self._networkops.create_nic(userid, vdev=vdev, nic_id=nic_id,
                                           mac_addr=mac_addr, active=active)

    @check_guest_exist()
    def guest_delete_nic(self, userid, vdev, active=False):
        """ delete the nic for the vm

        :param str userid: the user id of the vm
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether delete a nic on active guest system
        """
        self._networkops.delete_nic(userid, vdev, active=active)

    @check_guest_exist()
    def guest_get_definition_info(self, userid, **kwargs):
        """Get definition info for the specified guest vm, also could be used
        to check specific info.

        :param str userid: the user id of the guest vm
        :param dict kwargs: Dictionary used to check specific info in user
                            direct. Valid keywords for kwargs:
                            nic_coupled=<vdev>, where <vdev> is the virtual
                            device number of the nic to be checked the couple
                            status.
        :returns: Dictionary describing user direct and check info result
        :rtype: dict
        """
        action = "get the definition info of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.get_definition_info(userid, **kwargs)

    """Parse the nics' info from the user directory
    :param user_direct: (str) the user directory info to be parsed
    """
    def _parse_nic_info(self, user_direct):
        nics_info = {}
        for nic_info in user_direct:
            if nic_info.startswith('NICDEF'):
                split_info = nic_info.split()
                nic_id = split_info[1].strip()
                count = 2
                one_nic = nics_info.get(nic_id, {})
                while count < len(split_info):
                    if split_info[count] == 'LAN':
                        one_nic['vswitch'] = split_info[count + 2].strip()
                        count += 3
                        continue
                    elif split_info[count] == 'MACID':
                        one_nic['mac'] = split_info[count + 1].strip()
                        count += 2
                        continue
                    elif split_info[count] == 'VLAN':
                        one_nic['vid'] = split_info[count + 1].strip()
                        count += 2
                        continue
                    else:
                        count += 1

                nics_info[nic_id] = one_nic

        return nics_info

    def guest_register(self, userid, meta, net_set, port_macs=None):
        """Register vm by inserting or updating DB for e.g. migration and onboarding
        :param userid: (str) the userid of the vm to be relocated or tested
        :param meta: (str) the metadata of the vm to be relocated or tested
        :param net_set: (str) the net_set of the vm, default is 1.
        :param port_macs: (dict) the virtual interface port id maps with mac id
                     Format: { macid1 : portid1, macid2 : portid2}.
                     For example,
                     {
                       'EF5091':'6e2ecc4f-14a2-4f33-9f12-5ac4a42f97e7',
                       '69FCF1':'389dee5e-7b03-405c-b1e8-7c9c235d1425'
                     }
        """
        if port_macs is not None and not isinstance(port_macs, dict):
            msg = ('Invalid input parameter port_macs, expect dict')
            LOG.error(msg)
            raise exception.SDKInvalidInputFormat(msg)

        userid = userid.upper()
        if not zvmutils.check_userid_exist(userid):
            LOG.error("User directory '%s' does not exist." % userid)
            raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % userid), modID='guest')
        else:
            action = "query the guest in database."
            with zvmutils.log_and_reraise_sdkbase_error(action):
                guest = self._GuestDbOperator.get_guest_by_userid(userid)
            if guest is not None:
                # The below handling is for migration
                action = "list all guests in database which has been migrated."
                with zvmutils.log_and_reraise_sdkbase_error(action):
                    guests = self._GuestDbOperator.get_migrated_guest_list()
                if userid in str(guests):
                    """change comments for vm"""
                    comments = self._GuestDbOperator.get_comments_by_userid(
                                                                    userid)
                    comments['migrated'] = 0
                    action = "update guest '%s' in database" % userid
                    with zvmutils.log_and_reraise_sdkbase_error(action):
                        self._GuestDbOperator.update_guest_by_userid(userid,
                                                    comments=comments)
                    LOG.info("Guest %s comments updated." % userid)
                # We just return no matter onboarding or migration
                # since the guest exists
                return

            # add one record for new vm for both onboarding and migration,
            # and even others later.
            action = "add guest '%s' to database" % userid
            with zvmutils.log_and_reraise_sdkbase_error(action):
                self._GuestDbOperator.add_guest_registered(userid, meta,
                                                             net_set)

            # We need to query and add vswitch to the database.
            action = "add switches of guest '%s' to database" % userid
            # The result of get_adpaters_info
            # [{'adapter_address': '1000', 'adapter_status': '02',
            #   'lan_owner': 'SYSTEM', 'lan_name': 'VSC11590',
            #   'mac_address': '02:55:36:00:00:10', 'mac_ip_version': '4',
            #   'mac_ip_address': '9.152.85.95'}]
            adapters_info = self._smtclient.get_adapters_info(userid)
            for adapter in adapters_info:
                interface = adapter.get('adapter_address')
                switch = adapter.get('lan_name')
                port = None
                if port_macs is not None:
                    if adapter.get('mac_address'):
                        mac = ''.join(
                            adapter.get('mac_address').split(':'))[6:].upper()
                        if mac in port_macs.keys():
                            port = port_macs[mac]
                    if port is None:
                        LOG.warning("Port not found for nic %s, %s." %
                                    (interface, port_macs))
                    else:
                        LOG.info("Port found for nic %s." % interface)
                with zvmutils.log_and_reraise_sdkbase_error(action):
                    self._NetworkDbOperator.switch_add_record(
                                userid, interface, port, switch)
            LOG.info("Guest %s registered." % userid)

    # Deregister the guest (not delete), this function has no relationship with
    # migration.
    def guest_deregister(self, userid):
        """DB operation for deregister vm for offboard (dismiss) request.
        :param userid: (str) the userid of the vm to be deregistered
        """
        userid = userid.upper()
        # We don't check if the VM exists in the LPAR or zCC DB, just delete it
        # from DB anyway, cause there could be the case that the VM is deleted
        # outside of zCC e.g. smcli, and the DB record is still there.
        if not self._vmops.check_guests_exist_in_db(userid, raise_exc=False):
            LOG.warning("User directory '%s' does not exist in guest DB."
                        "But let's still delete it as there is also switch"
                        " table" % userid)
        action = "delete switches of guest '%s' from database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._NetworkDbOperator.switch_delete_record_for_userid(userid)

        action = "delete guest '%s' from database" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._GuestDbOperator.delete_guest_by_userid(userid)
        LOG.info("Guest %s deregistered." % userid)

    @check_guest_exist()
    def guest_live_migrate(self, userid, dest_zcc_userid, destination,
                           parms, lgr_action):
        """Move an eligible, running z/VM(R) virtual machine transparently
        from one z/VM system to another within an SSI cluster.

        :param userid: (str) the userid of the vm to be relocated or tested
        :param dest_zcc_userid: (str) the userid of zcc on destination.
               If None, no any userid is set into the guest.
        :param destination: (str) the system ID of the z/VM system to which
               the specified vm will be relocated or tested.
        :param parms: (dict) a dictionary of options for relocation.
               It has one dictionary that contains some of the below keys:
               {'maxtotal': i,
                'maxquiesce': i,
                'immediate': str}

                In which, 'maxtotal':indicates the maximum total time
                (in seconds)
                that the command issuer is willing to
                wait for the entire relocation
                to complete or -1 to indicate there is no limit for time.
                'maxquiesce':indicates the maximum quiesce time
                for this relocation.
                This is the amount of time (in seconds)
                a virtual machine may be stopped
                during a relocation attempt or -1 to indicate
                there is no limit for time.
                'immediate':If present, immediate=YES is set,
                which causes the VMRELOCATE command
                to do one early pass through virtual machine storage
                and then go directly to the quiesce stage.
        :param lgr_action: (str) indicates the action is move or test for vm.

        """
        if lgr_action.lower() == 'move':
            if dest_zcc_userid is None or dest_zcc_userid.strip() == '':
                msg = "dest_zcc_userid is empty so it will not be set " \
                      "during LGR."
                LOG.info(msg)

            # Live_migrate the guest
            operation = "Move guest '%s' to SSI '%s'" % (userid, destination)
            with zvmutils.log_and_reraise_sdkbase_error(operation):
                self._vmops.live_migrate_vm(userid, destination,
                                            parms, lgr_action)
            comments = self._GuestDbOperator.get_comments_by_userid(userid)
            comments['migrated'] = 1
            action = "update guest '%s' in database" % userid
            with zvmutils.log_and_reraise_sdkbase_error(action):
                self._GuestDbOperator.update_guest_by_userid(userid,
                                                    comments=comments)

            # Skip IUCV authorization for RHCOS guests
            is_rhcos = 'rhcos' in self._GuestDbOperator.get_guest_by_userid(
                            userid)[2].lower()
            if is_rhcos:
                LOG.debug("Skip IUCV authorization when migrating RHCOS "
                          "guests: %s" % userid)

            # Add authorization for new zcc.
            # This should be done after migration succeeds.
            # If the dest_zcc_userid is empty, nothing will be done because
            # this should be a onboarded guest and no permission to do it.
            if (dest_zcc_userid is not None and
                    dest_zcc_userid.strip() != '' and
                    not is_rhcos):
                cmd = ('echo -n %s > /etc/iucv_authorized_userid\n' %
                                                        dest_zcc_userid)
                rc = self._smtclient.execute_cmd(userid, cmd)
                if rc != 0:
                    err_msg = ("Add authorization for new zcc failed")
                    LOG.error(err_msg)

        if lgr_action.lower() == 'test':
            operation = "Test move guest '%s' to SSI '%s'" % (userid,
                                                    destination)
            with zvmutils.log_and_reraise_sdkbase_error(operation):
                self._vmops.live_migrate_vm(userid, destination,
                                            parms, lgr_action)

    def guest_create(self, userid, vcpus, memory, disk_list=None,
                     user_profile='',
                     max_cpu=CONF.zvm.user_default_max_cpu,
                     max_mem=CONF.zvm.user_default_max_memory,
                     ipl_from='', ipl_param='', ipl_loadparam='',
                     dedicate_vdevs=None, loaddev={}, account='',
                     comment_list=None, cschedule='', cshare='',
                     rdomain='', pcif=''):
        """create a vm in z/VM

        :param userid: (str) the userid of the vm to be created
        :param vcpus: (int) amount of vcpus
        :param memory: (int) size of memory in MB
        :param disk_list: (dict) a list of disks info for the guest.
               It has one dictionary that contain some of the below keys for
               each disk, the root disk should be the first element in the
               list, the format is:
               {'size': str,
               'format': str,
               'is_boot_disk': bool,
               'disk_pool': str}

               In which, 'size': case insensitive, the unit can be in
               Megabytes (M), Gigabytes (G), or number of cylinders/blocks, eg
               512M, 1g or just 2000.
               'format': can be ext2, ext3, ext4, xfs and none.
               'is_boot_disk': For root disk, this key must be set to indicate
               the image that will be deployed on this disk.
               'disk_pool': optional, if not specified, the disk will be
               created by using the value from configure file,the format is
               ECKD:eckdpoolname or FBA:fbapoolname.

               For example:
               [{'size': '1g',
               'is_boot_disk': True,
               'disk_pool': 'ECKD:eckdpool1'},
               {'size': '200000',
               'disk_pool': 'FBA:fbapool1',
               'format': 'ext3'},
               {'size': '1g',
                'format': 'ext3'}]
               In this case it will create one disk 0100(in case the vdev
               for root disk is 0100) with size 1g from ECKD disk pool
               eckdpool1 for guest , then set IPL 0100 in guest's user
               directory, and it will create 0101 with 200000 blocks from
               FBA disk pool fbapool1, and formated with ext3. As for the third
               case, if the disk_pool isn't configured in configure file, the
               default value is None, the disk_pool here is None, report error.
               If it's configured, such as ECKD:eckdpool2, it will
               create 0102 with size 1g from ECKD diskpool eckdpool2 for guest.
        :param user_profile: (str) the profile for the guest
        :param max_cpu: (int) the maximum number of virtual cpu this user can
               define. The value should be a decimal value between 1 and 64.
        :param max_mem: (str) the maximum size of memory the user can define.
               The value should be specified by 1-4 bits of number suffixed by
               either M (Megabytes) or G (Gigabytes). And the number should be
               an integer.
        :param ipl_from: (str) where to ipl the guest from, it can be given
               by guest input param, e.g CMS.
        :param ipl_param: the param to use when IPL for as PARM
        :param ipl_loadparam: the param to use when IPL for as LOADPARM
        :param dedicate_vdevs: (list) the list of device vdevs to dedicate to
               the guest.
        :param loaddev: (dict) the loaddev parms to add in the guest directory.
               Current supported key includes: 'portname', 'lun' and 'alterdev'.
               Both the 'portname' and 'lun' can specify only one one- to
               eight-byte hexadecimal value in the range of 0-FFFFFFFFFFFFFFFF
               The format should be:
               {'portname': str,
               'lun': str,
               'alterdev': str}
        :param account: (str) account string, see
        https://www.ibm.com/docs/en/zvm/6.4?topic=SSB27U_6.4.0/
                com.ibm.zvm.v640.hcpa5/daccoun.htm#daccoun
        :param comment_list: (array) a list of comment string
        :param cschedule: a command input for schedule cpu pool
        :param cshare: a command input for share settings
        :param rdomain: a command input for relocation domain
        :param pcif: a command input for pci function
        """
        dedicate_vdevs = dedicate_vdevs or []

        userid = userid.upper()
        if disk_list:

            # special case for swap disk, for boot from volume, might add swap
            # disk but not disk pool given, then we use vdisk instead
            swap_only = False
            if len(disk_list) == 1:
                disk = disk_list[0]
                if 'format' in disk and disk['format'].lower() == 'swap':
                    swap_only = True

            for disk in disk_list:
                if not isinstance(disk, dict):
                    errmsg = ('Invalid "disk_list" input, it should be a '
                              'dictionary. Details could be found in doc.')
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
                # 'size' is required for each disk
                if 'size' not in disk.keys():
                    errmsg = ('Invalid "disk_list" input, "size" is required '
                              'for each disk.')
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

                # check disk_pool
                disk_pool = disk.get('disk_pool')
                if disk_pool is None:
                    disk_pool = CONF.zvm.disk_pool
                    if disk_pool is not None:
                        disk_pools = disk_pool.split(",")
                        if len(disk_pools) == 1:
                            disk_pool = disk_pools[0]
                        else:
                            errmsg = ("disk_pool input is required if multiple disk_pool"
                                      " is configured for sdkserver.")
                            LOG.error(errmsg)
                            raise exception.SDKInvalidInputFormat(msg=errmsg)
                if not swap_only:
                    if disk_pool is None:
                        errmsg = ("Invalid disk_pool input, disk_pool should"
                                  " be configured for sdkserver.")
                        LOG.error(errmsg)
                        raise exception.SDKInvalidInputFormat(msg=errmsg)
                    # 'disk_pool' format check
                    if ':' not in disk_pool or (disk_pool.split(':')[0].upper()
                        not in ['ECKD', 'FBA']):
                        errmsg = ("Invalid disk_pool input, its format must be"
                                  " ECKD:eckdpoolname or FBA:fbapoolname")
                        LOG.error(errmsg)
                        raise exception.SDKInvalidInputFormat(msg=errmsg)
                else:
                    # in this case, it's swap only, and we will check whether
                    # no VDISK is allowed, if not allow, then return error
                    if disk_pool is None and CONF.zvm.swap_force_mdisk:
                        errmsg = ("Invalid disk_pool input, disk_pool should"
                                  " be configured for sdkserver and use"
                                  " VDISK as swap disk is not configured."
                                  " check CONF.zvm.swap_force_mdisk for"
                                  " additional information.")
                        LOG.error(errmsg)
                        raise exception.SDKInvalidInputFormat(msg=errmsg)

                # 'format' value check
                if ('format' in disk.keys()) and (disk['format'].lower() not in
                                                  ('ext2', 'ext3', 'ext4',
                                                  'swap', 'xfs', 'none')):
                    errmsg = ("Invalid disk_pool input, supported 'format' "
                              "includes 'ext2', 'ext3', 'ext4', 'xfs', "
                              "'swap', 'none'")
                    LOG.error(errmsg)
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

        if dedicate_vdevs and not isinstance(dedicate_vdevs, list):
            errmsg = ('Invalid "dedicate_vdevs" input, it should be a '
                              'list. Details could be found in doc.')
            LOG.error(errmsg)
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        if loaddev and not isinstance(loaddev, dict):
            errmsg = ('Invalid "loaddev" input, it should be a '
                              'dictionary. Details could be found in doc.')
            LOG.error(errmsg)
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        if not user_profile or len(user_profile) == 0:
            user_profile = CONF.zvm.user_profile
            if not user_profile:
                errmsg = ('Invalid "user_profile" input, user_profile  '
                        'cannot be empty.')
                LOG.error(errmsg)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        action = "create guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.create_vm(userid, vcpus, memory, disk_list,
                                         user_profile, max_cpu, max_mem,
                                         ipl_from, ipl_param, ipl_loadparam,
                                         dedicate_vdevs, loaddev, account,
                                         comment_list, cschedule, cshare,
                                         rdomain, pcif)

    @check_guest_exist()
    def guest_live_resize_cpus(self, userid, cpu_cnt, cpu_share=''):
        """Live resize virtual cpus of guests.

        :param userid: (str) the userid of the guest to be live resized
        :param cpu_cnt: (int) The number of virtual cpus that the guest should
               have in active state after live resize. The value should be an
               integer between 1 and 64.

        """
        action = "live resize guest '%s' to have '%i' virtual cpus" % (userid,
                                                                       cpu_cnt)
        LOG.info("Begin to %s" % action)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.live_resize_cpus(userid, cpu_cnt, cpu_share)
        LOG.info("%s successfully." % action)

    @check_guest_exist()
    def guest_resize_cpus(self, userid, cpu_cnt, cpu_share=''):
        """Resize virtual cpus of guests.

        :param userid: (str) the userid of the guest to be resized
        :param cpu_cnt: (int) The number of virtual cpus that the guest should
               have defined in user directory after resize. The value should
               be an integer between 1 and 64.

        """
        action = "resize guest '%s' to have '%i' virtual cpus" % (userid,
                                                                  cpu_cnt)
        LOG.info("Begin to %s" % action)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.resize_cpus(userid, cpu_cnt, cpu_share)
        LOG.info("%s successfully." % action)

    @check_guest_exist()
    def guest_live_resize_mem(self, userid, size):
        """Live resize memory of guests.

        :param userid: (str) the userid of the guest to be live resized
        :param size: (str) The memory size that the guest should have
               in available status after live resize.
               The value should be specified by 1-4 bits of number suffixed by
               either M (Megabytes) or G (Gigabytes). And the number should be
               an integer.

        """
        action = "live resize guest '%s' to have '%s' memory" % (userid,
                                                                 size)
        LOG.info("Begin to %s" % action)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.live_resize_memory(userid, size)
        LOG.info("%s successfully." % action)

    @check_guest_exist()
    def guest_resize_mem(self, userid, size):
        """Resize memory of guests.

        :param userid: (str) the userid of the guest to be resized
        :param size: (str) The memory size that the guest should have
               defined in user directory after resize.
               The value should be specified by 1-4 bits of number suffixed by
               either M (Megabytes) or G (Gigabytes). And the number should be
               an integer.

        """
        action = "resize guest '%s' to have '%s' memory" % (userid, size)
        LOG.info("Begin to %s" % action)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.resize_memory(userid, size)
        LOG.info("%s successfully." % action)

    @check_guest_exist()
    def guest_create_disks(self, userid, disk_list):
        """Add disks to an existing guest vm.

        :param userid: (str) the userid of the vm to be created
        :param disk_list: (list) a list of disks info for the guest.
               It has one dictionary that contain some of the below keys for
               each disk, the root disk should be the first element in the
               list, the format is:
               {'size': str,
               'format': str,
               'is_boot_disk': bool,
               'disk_pool': str}

               In which, 'size': case insensitive, the unit can be in
               Megabytes (M), Gigabytes (G), or number of cylinders/blocks, eg
               512M, 1g or just 2000.
               'format': optional, can be ext2, ext3, ext4, xfs, if not
               specified, the disk will not be formatted.
               'is_boot_disk': For root disk, this key must be set to indicate
               the image that will be deployed on this disk.
               'disk_pool': optional, if not specified, the disk will be
               created by using the value from configure file,the format is
               ECKD:eckdpoolname or FBA:fbapoolname.

               For example:
               [{'size': '1g',
               'is_boot_disk': True,
               'disk_pool': 'ECKD:eckdpool1'},
               {'size': '200000',
               'disk_pool': 'FBA:fbapool1',
               'format': 'ext3'},
               {'size': '1g',
                'format': 'ext3'}]
               In this case it will create one disk 0100(in case the vdev
               for root disk is 0100) with size 1g from ECKD disk pool
               eckdpool1 for guest , then set IPL 0100 in guest's user
               directory, and it will create 0101 with 200000 blocks from
               FBA disk pool fbapool1, and formated with ext3. As for the third
               case, if the disk_pool isn't configured in configure file, the
               default value is None, the disk_pool here is None, report error.
               If it's configured, such as ECKD:eckdpool2, it will
               create 0102 with size 1g from ECKD diskpool eckdpool2 for guest.
        """
        if disk_list == [] or disk_list is None:
            # nothing to do
            LOG.debug("No disk specified when calling guest_create_disks, "
                      "nothing happened")
            return

        for disk in disk_list:
            if not isinstance(disk, dict):
                errmsg = ('Invalid "disk_list" input, it should be a '
                          'dictionary. Details could be found in doc.')
                LOG.error(errmsg)
                raise exception.SDKInvalidInputFormat(msg=errmsg)
            # check disk_pool
            disk_pool = disk.get('disk_pool')
            if disk_pool is None:
                disk_pool = CONF.zvm.disk_pool
                if disk_pool is not None:
                    disk_pools = disk_pool.split(",")
                    if len(disk_pools) == 1:
                        disk_pool = disk_pools[0]
                    else:
                        errmsg = ("disk_pool input is required if multiple disk_pool"
                                  " is configured for sdkserver.")
                        LOG.error(errmsg)
                        raise exception.SDKInvalidInputFormat(msg=errmsg)

            if disk_pool is None:
                errmsg = ("Invalid disk_pool input, it should be configured"
                          " for sdkserver.")
                LOG.error(errmsg)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        action = "create disks '%s' for guest '%s'" % (str(disk_list), userid)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.create_disks(userid, disk_list)

    @check_guest_exist()
    def guest_delete_disks(self, userid, disk_vdev_list):
        """Delete disks from an existing guest vm.

        :param userid: (str) the userid of the vm to be deleted
        :param disk_vdev_list: (list) the vdev list of disks to be deleted,
            for example: ['0101', '0102']
        """
        action = "delete disks '%s' from guest '%s'" % (str(disk_vdev_list),
                                                        userid)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.delete_disks(userid, disk_vdev_list)

    @check_guest_exist()
    def guest_nic_couple_to_vswitch(self, userid, nic_vdev,
                                    vswitch_name, active=False, vlan_id=-1):
        """ Couple nic device to specified vswitch.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param str vswitch_name: the name of the vswitch
        :param bool active: whether make the change on active guest system
        :param str vlan_id: the VLAN ID of the NIC
        """
        self._networkops.couple_nic_to_vswitch(userid, nic_vdev,
                                               vswitch_name, active=active,
                                               vlan_id=vlan_id)

    @check_guest_exist()
    def guest_nic_uncouple_from_vswitch(self, userid, nic_vdev,
                                        active=False):
        """ Disonnect nic device with network.

        :param str userid: the user's name who owns the nic
        :param str nic_vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether make the change on active guest system
        """
        self._networkops.uncouple_nic_from_vswitch(userid, nic_vdev,
                                                   active=active)

    def vswitch_get_list(self):
        """ Get the vswitch list.

        :returns: vswitch name list
        :rtype: list
        """
        return self._networkops.get_vswitch_list()

    def vswitch_create(self, name, rdev=None, controller='*',
                       connection='CONNECT', network_type='ETHERNET',
                       router="NONROUTER", vid='UNAWARE', port_type='ACCESS',
                       gvrp='GVRP', queue_mem=8, native_vid=1,
                       persist=True):
        """ Create vswitch.

        :param str name: the vswitch name
        :param str rdev: the real device number, a maximum of three devices,
               all 1-4 characters in length, delimited by blanks. 'NONE'
               may also be specified
        :param str controller: the vswitch's controller, it could be the userid
               controlling the real device, or '*' to specifies that any
               available controller may be used
        :param str connection:
            - CONnect:
                Activate the real device connection.
            - DISCONnect:
                Do not activate the real device connection.
            - NOUPLINK:
                The vswitch will never have connectivity through
                the UPLINK port
        :param str network_type: Specifies the transport mechanism to be used
               for the vswitch, as follows: IP, ETHERNET
        :param str router:
            - NONrouter:
                The OSA-Express device identified in
                real_device_address= will not act as a router to the
                vswitch
            - PRIrouter:
                The OSA-Express device identified in
                real_device_address= will act as a primary router to the
                vswitch
            - Note: If the network_type is ETHERNET, this value must be
                unspecified, otherwise, if this value is unspecified, default
                is NONROUTER
        :param str/int vid: the VLAN ID. This can be any of the following
               values: UNAWARE, AWARE or 1-4094
        :param str port_type:
            - ACCESS:
                The default porttype attribute for
                guests authorized for the virtual switch.
                The guest is unaware of VLAN IDs and sends and
                receives only untagged traffic
            - TRUNK:
                The default porttype attribute for
                guests authorized for the virtual switch.
                The guest is VLAN aware and sends and receives tagged
                traffic for those VLANs to which the guest is authorized.
                If the guest is also authorized to the natvid, untagged
                traffic sent or received by the guest is associated with
                the native VLAN ID (natvid) of the virtual switch.
        :param str gvrp:
            - GVRP:
                Indicates that the VLAN IDs in use on the virtual
                switch should be registered with GVRP-aware switches on the
                LAN. This provides dynamic VLAN registration and VLAN
                registration removal for networking switches. This
                eliminates the need to manually configure the individual
                port VLAN assignments.
            - NOGVRP:
                Do not register VLAN IDs with GVRP-aware switches on
                the LAN. When NOGVRP is specified VLAN port assignments
                must be configured manually
        :param int queue_mem: A number between 1 and 8, specifying the QDIO
               buffer size in megabytes.
        :param int native_vid: the native vlan id, 1-4094 or None
        :param bool persist: whether create the vswitch in the permanent
               configuration for the system
        """
        if ((queue_mem < 1) or (queue_mem > 8)):
            errmsg = ('API vswitch_create: Invalid "queue_mem" input, '
                      'it should be 1-8')
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        if isinstance(vid, int) or vid.upper() != 'UNAWARE':
            if ((native_vid is not None) and
                ((native_vid < 1) or (native_vid > 4094))):
                errmsg = ('API vswitch_create: Invalid "native_vid" input, '
                          'it should be 1-4094 or None')
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        if network_type.upper() == 'ETHERNET':
            router = None

        self._networkops.add_vswitch(name, rdev=rdev, controller=controller,
                                     connection=connection,
                                     network_type=network_type,
                                     router=router, vid=vid,
                                     port_type=port_type, gvrp=gvrp,
                                     queue_mem=queue_mem,
                                     native_vid=native_vid,
                                     persist=persist)

    @check_guest_exist()
    def guest_get_console_output(self, userid):
        """Get the console output of the guest virtual machine.

        :param str userid: the user id of the vm
        :returns: console log string
        :rtype: str
        """
        action = "get the console output of guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            output = self._vmops.get_console_output(userid)

        return output

    def guest_delete(self, userid):
        """Delete guest.

        :param userid: the user id of the vm
        """

        # check guest exist in database or not
        userid = userid.upper()
        if not self._vmops.check_guests_exist_in_db(userid, raise_exc=False):
            if zvmutils.check_userid_exist(userid):
                LOG.error("Guest '%s' does not exist in guests database" %
                          userid)
                raise exception.SDKObjectNotExistError(
                    obj_desc=("Guest '%s'" % userid), modID='guest')
            else:
                LOG.debug("The guest %s does not exist." % userid)
                return

        action = "delete guest '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._vmops.delete_vm(userid)

    @check_guest_exist()
    def guest_inspect_stats(self, userid_list):
        """Get the statistics including cpu and mem of the guests

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the cpu statistics of the vm
                  in the form {'UID1':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx,
                  'used_mem_kb': xx,
                  'max_mem_kb': xx,
                  'min_mem_kb': xx,
                  'shared_mem_kb': xx
                  },
                  'UID2':
                  {
                  'guest_cpus': xx,
                  'used_cpu_time_us': xx,
                  'elapsed_cpu_time_us': xx,
                  'min_cpu_count': xx,
                  'max_cpu_limit': xx,
                  'samples_cpu_in_use': xx,
                  'samples_cpu_delay': xx,
                  'used_mem_kb': xx,
                  'max_mem_kb': xx,
                  'min_mem_kb': xx,
                  'shared_mem_kb': xx
                  }
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        action = "get the statistics of guest '%s'" % str(userid_list)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._monitor.inspect_stats(userid_list)

    @check_guest_exist()
    def guest_inspect_vnics(self, userid_list):
        """Get the vnics statistics of the guest virtual machines

        :param userid_list: a single userid string or a list of guest userids
        :returns: dictionary describing the vnics statistics of the vm
                  in the form
                  {'UID1':
                  [{
                  'vswitch_name': xx,
                  'nic_vdev': xx,
                  'nic_fr_rx': xx,
                  'nic_fr_tx': xx,
                  'nic_fr_rx_dsc': xx,
                  'nic_fr_tx_dsc': xx,
                  'nic_fr_rx_err': xx,
                  'nic_fr_tx_err': xx,
                  'nic_rx': xx,
                  'nic_tx': xx
                  },
                  ],
                  'UID2':
                  [{
                  'vswitch_name': xx,
                  'nic_vdev': xx,
                  'nic_fr_rx': xx,
                  'nic_fr_tx': xx,
                  'nic_fr_rx_dsc': xx,
                  'nic_fr_tx_dsc': xx,
                  'nic_fr_rx_err': xx,
                  'nic_fr_tx_err': xx,
                  'nic_rx': xx,
                  'nic_tx': xx
                  },
                  ]
                  }
                  for the guests that are shutdown or not exist, no data
                  returned in the dictionary
        """
        if not isinstance(userid_list, list):
            userid_list = [userid_list]
        action = "get the vnics statistics of guest '%s'" % str(userid_list)
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._monitor.inspect_vnics(userid_list)

    @check_guest_exist(check_index=1)
    def vswitch_grant_user(self, vswitch_name, userid):
        """Set vswitch to grant user

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """

        self._networkops.grant_user_to_vswitch(vswitch_name, userid)

    def vswitch_revoke_user(self, vswitch_name, userid):
        """Revoke user for vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        """
        self._networkops.revoke_user_from_vswitch(vswitch_name, userid)

    def get_switch_info(self, portid):
        """get switch information based on portid

        :param str portid: the id of the port
        :returns: list includes  switch db record information.
                  [{'userid': 'WGNZ0046', 'interface': '4000', 'switch': 'VSICIC',
                  'port': '61343f8c-dc88-41b2-be74-ad81fe018856', 'comments': None}]
        """
        return self._networkops.get_switch_info(portid)

    @check_guest_exist(check_index=1)
    def vswitch_set_vlan_id_for_user(self, vswitch_name, userid, vlan_id):
        """Set vlan id for user when connecting to the vswitch

        :param str vswitch_name: the name of the vswitch
        :param str userid: the user id of the vm
        :param int vlan_id: the VLAN id
        """
        self._networkops.set_vswitch_port_vlan_id(vswitch_name,
                                                  userid, vlan_id)

    @check_guest_exist()
    def guest_config_minidisks(self, userid, disk_info):
        """Punch the script that used to process additional disks to vm

        :param str userid: the user id of the vm
        :param disk_info: a list contains disks info for the guest. It
               contains dictionaries that describes disk info for each disk.

               Each dictionary has 3 keys, format is required, vdev and
               mntdir are optional. For example, if vdev is not specified, it
               will start from the next vdev of CONF.zvm.user_root_vdev, eg.
               if CONF.zvm.user_root_vdev is 0100, zvmsdk will use 0101 as the
               vdev for first additional disk in disk_info, and if mntdir is
               not specified, zvmsdk will use /mnt/ephemeral0 as the mount
               point of first additional disk

               Here are some examples:
               [{'vdev': '0101',
               'format': 'ext3',
               'mntdir': '/mnt/ephemeral0'}]
               In this case, the zvmsdk will treat 0101 as additional disk's
               vdev, and it's formatted with ext3, and will be mounted to
               /mnt/ephemeral0

               [{'format': 'ext3'},
               {'format': 'ext4'}]
               In this case, if CONF.zvm.user_root_vdev is 0100, zvmsdk will
               configure the first additional disk as 0101, mount it to
               /mnt/ephemeral0 with ext3, and configure the second additional
               disk 0102, mount it to /mnt/ephemeral1 with ext4.

        """
        action = "config disks for userid '%s'" % userid
        with zvmutils.log_and_reraise_sdkbase_error(action):
            self._vmops.guest_config_minidisks(userid, disk_info)

    @check_guest_exist()
    def guest_grow_root_volume(self, userid, os_version):
        """ Punch script to guest to grow root partition and extend
            root file system.
            Note:
            1. Only multipath SCSI disk is supported.
            2. Only one partition is supported.
            3. xfs file system is not supported.

        :param str userid: the user id of the vm
        :param str os_version: operating system version of the guest
        """
        return self._vmops.guest_grow_root_volume(userid, os_version)

    def vswitch_set(self, vswitch_name, **kwargs):
        """Change the configuration of an existing virtual switch

        :param str vswitch_name: the name of the virtual switch
        :param dict kwargs:
            - grant_userid=<value>:
                A userid to be added to the access list
            - user_vlan_id=<value>:
                user VLAN ID. Support following ways:
                1. As single values between 1 and 4094. A maximum of four
                values may be specified, separated by blanks.
                Example: 1010 2020 3030 4040
                2. As a range of two numbers, separated by a dash (-).
                A maximum of two ranges may be specified.
                Example: 10-12 20-22
            - revoke_userid=<value>:
                A userid to be removed from the access list
            - real_device_address=<value>:
                The real device address or the real device address and
                OSA Express port number of a QDIO OSA
                Express device to be used to create the switch to the virtual
                adapter. If using a real device and an OSA Express port number,
                specify the real device number followed by a period(.),
                the letter 'P' (or 'p'), followed by the port number as a
                hexadecimal number. A maximum of three device addresses,
                all 1-7 characters in length, may be specified, delimited by
                blanks. 'None' may also be specified
            - port_name=<value>:
                The name used to identify the OSA Expanded
                adapter. A maximum of three port names, all 1-8 characters in
                length, may be specified, delimited by blanks.
            - controller_name=<value>:
                One of the following:
                1. The userid controlling the real device. A maximum of eight
                userids, all 1-8 characters in length, may be specified,
                delimited by blanks.
                2. '*': Specifies that any available controller may be used
            - connection_value=<value>:
                One of the following values:
                CONnect: Activate the real device connection.
                DISCONnect: Do not activate the real device connection.
            - queue_memory_limit=<value>:
                A number between 1 and 8
                specifying the QDIO buffer size in megabytes.
            - routing_value=<value>:
                Specifies whether the OSA-Express QDIO
                device will act as a router to the virtual switch, as follows:
                NONrouter: The OSA-Express device identified in
                real_device_address= will not act as a router to the vswitch
                PRIrouter: The OSA-Express device identified in
                real_device_address= will act as a primary router to the
                vswitch
            - port_type=<value>:
                Specifies the port type, ACCESS or TRUNK
            - persist=<value>:
                one of the following values:
                NO: The vswitch is updated on the active system, but is not
                updated in the permanent configuration for the system.
                YES: The vswitch is updated on the active system and also in
                the permanent configuration for the system.
                If not specified, the default is NO.
            - gvrp_value=<value>:
                GVRP or NOGVRP
            - mac_id=<value>:
                A unique identifier (up to six hexadecimal
                digits) used as part of the vswitch MAC address
            - uplink=<value>:
                One of the following:
                NO: The port being enabled is not the vswitch's UPLINK port.
                YES: The port being enabled is the vswitch's UPLINK port.
            - nic_userid=<value>:
                One of the following:
                1. The userid of the port to/from which the UPLINK port will
                be connected or disconnected. If a userid is specified,
                then nic_vdev= must also be specified
                2. '*': Disconnect the currently connected guest port to/from
                the special virtual switch UPLINK port. (This is equivalent
                to specifying NIC NONE on CP SET VSWITCH).
            - nic_vdev=<value>:
                The virtual device to/from which the the
                UPLINK port will be connected/disconnected. If this value is
                specified, nic_userid= must also be specified, with a userid.
            - lacp=<value>:
                One of the following values:
                ACTIVE: Indicates that the virtual switch will initiate
                negotiations with the physical switch via the link aggregation
                control protocol (LACP) and will respond to LACP packets sent
                by the physical switch.
                INACTIVE: Indicates that aggregation is to be performed,
                but without LACP.
            - Interval=<value>:
                The interval to be used by the control
                program (CP) when doing load balancing of conversations across
                multiple links in the group. This can be any of the following
                values:
                1 - 9990: Indicates the number of seconds between load
                balancing operations across the link aggregation group.
                OFF: Indicates that no load balancing is done.
            - group_rdev=<value>:
                The real device address or the real device
                address and OSA Express port number of a QDIO OSA Express
                devcie to be affected within the link aggregation group
                associated with this vswitch. If using a real device and an OSA
                Express port number, specify the real device number followed
                by a period (.), the letter 'P' (or 'p'), followed by the port
                number as a hexadecimal number. A maximum of eight device
                addresses all 1-7 characters in length, may be specified,
                delimited by blanks.
                Note: If a real device address is specified, this device will
                be added to the link aggregation group associated with this
                vswitch. (The link aggregation group will be created if it does
                not already exist.)
            - iptimeout=<value>:
                A number between 1 and 240 specifying the
                length of time in minutes that a remote IP address table entry
                remains in the IP address table for the virtual switch.
            - port_isolation=<value>:
                ON or OFF
            - promiscuous=<value>:
                One of the following:
                NO: The userid or port on the grant is not authorized to use
                the vswitch in promiscuous mode
                YES: The userid or port on the grant is authorized to use the
                vswitch in promiscuous mode.
            - MAC_protect=<value>:
                ON, OFF or UNSPECified
            - VLAN_counters=<value>:
                ON or OFF
        """
        for k in kwargs.keys():
            if k not in constants.SET_VSWITCH_KEYWORDS:
                errmsg = ('API vswitch_set: Invalid keyword %s' % k)
                raise exception.SDKInvalidInputFormat(msg=errmsg)

        self._networkops.set_vswitch(vswitch_name, **kwargs)

    def vswitch_delete(self, vswitch_name, persist=True):
        """ Delete vswitch.

        :param str name: the vswitch name
        :param bool persist: whether delete the vswitch from the permanent
               configuration for the system
        """
        self._networkops.delete_vswitch(vswitch_name, persist)

    def get_volume_connector(self, userid, reserve=False,
                             fcp_template_id=None, sp_name=None, pchid_info=dict()):
        """Get connector information of the instance for attaching or detaching volumes.
        This API is for Openstack Cinder driver only now.

        @param userid: (str) instance userid in z/VM
        @param reserve: (bool) True for attach-volume process, False for detach-volume
        @param fcp_template_id: (str) FCP multipath template ID
        @param sp_name: (str) storage provider hostname
        @param pchid_info: (dict) it is only needed when reserve is True.
            PCHID as key,
            'allocated' means the count of allocated FCP devices from the PCHID
            'max' means the maximum allowable count of FCP devices that can be allocated from the PCHID
            example:
            {'AAAA': {'allocated': 126, 'max': 128},
             'BBBB': {'allocated': 109, 'max': 110},
             'CCCC': {'allocated': 111, 'max': 128},
             'DDDD': {'allocated': 113, 'max': 110},
             'EEEE': {'allocated': 70,  'max': 90}}
        @return: (dict)
            example:
            {
                'zvm_fcp': [fcp1, fcp2, fcp3]
                'wwpns': [npiv_wwpn1, npiv_wwpn2, npiv_wwpn3]
                'phy_to_virt_initiators':{
                    npiv_wwpn1: phy_wwpn1,
                    npiv_wwpn2: phy_wwpn2,
                    npiv_wwpn3: phy_wwpn3
                }
                'host': LPARname_VMuserid, # the name to be used by storage provider
                'fcp_paths': 3,            # the count of fcp paths
                'fcp_template_id': '123',  # if user doesn't specify it,
                                             it is either the SP default or the host
                                             default template id
                'cpc_sn': '8257',
                'cpc_name': 'M54',
                'lpar': 'ZVM4OCP1',
                "hypervisor_hostname": "BOEM5401",
                'pchid_fcp_map': {
                    'A': [fcp1, fcp2],
                    'B': [fcp3]
                },
                'is_reserved_changed': True  # True for either attaching 1st volume to
                                               or detaching last volume from
                                               the VM (assigner_id)
                                               through this template (fcp_template_id)
            }
        """
        return self._volumeop.get_volume_connector(
            userid, reserve,
            fcp_template_id=fcp_template_id, sp_name=sp_name, pchid_info=pchid_info)

    def get_fcp_templates(self, template_id_list=None, assigner_id=None,
                         default_sp_list= None, host_default=None):
        """Get template base info
        :param template_id_list: (list) a list of template id,
        if it is None, get FCP Multipath Templates with other parameter
        :param assigner_id: (str) a string of VM userid
        :param host_default: (boolean) whether or not get host default fcp
        template
        :param default_sp_list: (list) a list of storage provider, to get the
        list of storage provider's default FCP Multipath Templates
        :return: (dict) the base info of template
        example:
        {
            templates: [
                {
                    name: t1,
                    id: template1_id,
                    description: description,
                    host_default: 0,
                    sp_default: [sp1]
                },
                {
                    name: t2,
                    id: template2_id,
                    description: description,
                    host_default: 1,
                    sp_default: [sp1, sp2]
                }
            ]
        }
        """
        # pass in template_id_list and default_sp_list is string:
        # "['36439338-db14-11ec-bb41-0201018b1dd2']"
        # convert to list
        if template_id_list and not isinstance(template_id_list, list):
            template_id_list = ast.literal_eval(template_id_list)
        if default_sp_list and not isinstance(default_sp_list, list):
            default_sp_list = ast.literal_eval(default_sp_list)

        return self._volumeop.get_fcp_templates(
            template_id_list=template_id_list, assigner_id=assigner_id,
            default_sp_list=default_sp_list, host_default=host_default)

    def get_fcp_templates_details(self, template_id_list=None,
                                  raw=False, statistics=True,
                                  sync_with_zvm=False):
        """Get FCP Multipath Templates detail info.
        :param template_list: (list) if is None,
                              will get all the templates on the host
        :return: (dict) the raw and/or statistic data
                        of temlate_list FCP devices
        if sync_with_zvm:
            self.fcp_mgr._sync_db_with_zvm()
        if FCP DB is NOT empty and raw=True statistics=True
        {
            "fcp_templates":[
                {
                    "id":"36439338-db14-11ec-bb41-0201018b1dd2",
                    "name":"default_template",
                    "description":"This is Default template",
                    "is_default":True,
                    "sp_name":[
                        "sp4",
                        "v7k60"
                    ],
                    "raw":{
                        # (fcp_id, template_id, assigner_id, connections,
                        #  reserved, wwpn_npiv, wwpn_phy, chpid, state, owner,
                        #  tmpl_id)
                        "0":[
                            [
                                "1a0f",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "HLP0000B",
                                0,
                                0,
                                "c05076de3300038b",
                                "c05076de33002e41",
                                "27",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ],
                            [
                                "1a0e",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "",
                                0,
                                0,
                                "c05076de330003a2",
                                "c05076de33002e41",
                                "27",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ]
                        ],
                        "1":[
                            [
                                "1c0d",
                                "36439338-db14-11ec-bb41-0201018b1dd2",
                                "",
                                0,
                                0,
                                "c05076de33000353",
                                "c05076de33002641",
                                "32",
                                "free",
                                "none",
                                "36439338-db14-11ec-bb41-0201018b1dd2"
                            ]
                        ]
                    },
                    "statistics":{
                        "0":{
                            "total":"1A0E - 1A0F",
                            "available":"1A0E - 1A0F",
                            "allocated":"",
                            "reserve_only":"",
                            "connection_only":"",
                            "unallocated_but_active":[

                            ],
                            "allocated_but_free":"",
                            "notfound":"",
                            "offline":"",
                            "CHPIDs":{
                                "27":"1A0E - 1A0F"
                            }
                        },
                        "1":{
                            "total":"1C0D",
                            "available":"1C0D",
                            "allocated":"",
                            "reserve_only":"",
                            "connection_only":"",
                            "unallocated_but_active":[

                            ],
                            "allocated_but_free":"",
                            "notfound":"",
                            "offline":"",
                            "CHPIDs":{
                                "32":"1C0D"
                            }
                        }
                    }
                }
            ]
        }
        """
        # pass in template_id_list is string:
        # "['36439338-db14-11ec-bb41-0201018b1dd2']"
        # convert to list
        if template_id_list and not isinstance(template_id_list, list):
            template_id_list = ast.literal_eval(template_id_list)

        return self._volumeop.get_fcp_templates_details(
            template_id_list=template_id_list, raw=raw,
            statistics=statistics, sync_with_zvm=sync_with_zvm)

    def delete_fcp_template(self, template_id):
        return self._volumeop.delete_fcp_template(template_id)

    @check_fcp_exist()
    def get_fcp_usage(self, fcp):
        """API for getting FCP usage in database manually.

        :param str userid: the user id of the guest
        :param str fcp: the fcp ID of FCP device

        :returns: list describing reserved,connections values of the FCP
                  in database. For example,
                  ['fakeid', 1, 3, 'b7ad5cba-f225-11ec-a5cf-02553600000f'] means
                  the userid is fakeid, reserved value is 1, connections is 3,
                  fcp_template_id is 'b7ad5cba-f225-11ec-a5cf-02553600000f'.
        """
        return self._volumeop.get_fcp_usage(fcp)

    @check_fcp_exist()
    def set_fcp_usage(self, fcp, userid, reserved, connections,
                      fcp_template_id):
        """API for setting FCP usage in database manually.

        :param str userid: the user id of the guest
        :param str fcp: the fcp ID of FCP device
        :param int reserved: the value set to reserved value of FCP database
        :param int connections: the value set to connections value of
                                FCP database
        :param str fcp_template_id: the ID of the FCP Multipath Template.
        """
        return self._volumeop.set_fcp_usage(userid, fcp, reserved,
                                            connections, fcp_template_id)

    def create_fcp_template(self, name, description: str = '',
                            fcp_devices: str = '',
                            host_default: bool = False,
                            default_sp_list: list = [],
                            min_fcp_paths_count: int = None):
        """API for creating a FCP Multipath Template in database.

        :param str name: the name of the template
        :param str description: the description for the template
        :param str fcp_devices: a fcp list is composed of fcp device IDs,
            range indicator '-', and split indicator ';'.
        :param bool host_default: this template is default to this
            host or not
        :param list default_sp_list: the list of storage providers that will
            use this FCP Multipath Template as default FCP Multipath Template. If None, it means
            no storage provider would use this FCP Multipath Template as default.
        :param min_fcp_paths_count: The minimum number of FCP paths that
            should be defined to a vm when attachinga data volume to a vm or
            BFV (deploying a vm from SCSI image).
        """
        return self._volumeop.create_fcp_template(
            name, description, fcp_devices,
            host_default=host_default, default_sp_list=default_sp_list, min_fcp_paths_count=min_fcp_paths_count)

    def edit_fcp_template(self, fcp_template_id, name=None,
                          description=None, fcp_devices=None,
                          host_default=None, default_sp_list=None, min_fcp_paths_count: int = None):
        """ Edit a FCP Multipath Template.

        The kwargs values are pre-validated in two places:
          validate kwargs types
            in zvmsdk/sdkwsgi/schemas/volume.py
          set a kwarg as None if not passed by user
            in zvmsdk/sdkwsgi/handlers/volume.py

        If any kwarg is None, the kwarg will not be updated.

        :param fcp_template_id: template id
        :param name:            template name
        :param description:     template desc
        :param fcp_devices:     FCP devices divided into
                                different paths by semicolon
          Format:
            "fcp-devices-from-path0;fcp-devices-from-path1;..."
          Example:
            "0011-0013;0015;0017-0018",
        :param host_default: (bool)
        :param default_sp_list: (list)
          Example:
            ["SP1", "SP2"]
        :param min_fcp_paths_count: min fcp paths count
        :return:
          Example
            {
              'fcp_template': {
                'name': 'bjcb-test-template',
                'id': '36439338-db14-11ec-bb41-0201018b1dd2',
                'description': 'This is Default template',
                'is_default': True,
                'sp_name': ['sp4', 'v7k60']
            }
            }
        """
        return self._volumeop.edit_fcp_template(
            fcp_template_id, name=name, description=description,
            fcp_devices=fcp_devices, host_default=host_default,
            default_sp_list=default_sp_list, min_fcp_paths_count=min_fcp_paths_count)

    def volume_attach(self, connection_info):
        """ Attach a volume to a guest. It's prerequisite to active multipath
            feature on the guest before utilizing persistent volumes.

        :param dict connection_info:
                - alias: of type string. A constant valid alias of the volume
                    after it being attached onto the guest, i.e. '/dev/vda'.
                    Because the system generating device name could change
                    after each rebooting, it's necessary to have a constant
                    name to represent the volume in its life time.
                - protocol: of type string. The protocol by which the volume is
                    connected to the guest. The only one supported now is 'fc'
                    which implies FibreChannel.
                - fcps: of type list. The address of the FCP devices used by
                    the guest to connect to the volume. They should belong to
                    different channel path IDs in order to work properly.
                - wwpns: of type list. The WWPN values through which the volume
                    can be accessed, excluding prefixing '0x'.
                - dedicate: of type list. The address of the FCP devices which
                    will be dedicated to the guest before accessing the volume.
                    They should belong to different channel path IDs in order
                    to work properly.
        """
        self._volumeop.attach_volume_to_instance(connection_info)

    def volume_refresh_bootmap(self, fcpchannels, wwpns, lun,
                               wwid='',
                               transportfiles=None, guest_networks=None, fcp_template_id=None):
        """ Refresh a volume's bootmap info.

        :param list of fcpchannels
        :param list of wwpns
        :param string lun
        :param wwid: (str) the wwid of the target volume
        :param transportfiles: (str) the files that used to customize the vm
        :param list guest_networks: a list of network info for the guest.
               It has one dictionary that contain some of the below keys for
               each network, the format is:
               {'ip_addr': (str) IP address or None,
               'dns_addr': (list) dns addresses or None,
               'gateway_addr': (str) gateway address or None,
               'cidr': (str) cidr format,
               'nic_vdev': (str)nic VDEV, 1- to 4- hexadecimal digits or None,
               'nic_id': (str) nic identifier or None,
               'mac_addr': (str) mac address or None, it is only be used when
               changing the guest's user direct. Format should be
               xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit
               'osa_device': (str) OSA address or None,
               'hostname': (str) Optional. The hostname of the guest}

               Example for guest_networks:
               [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mac_addr': '02:00:00:12:34:56',
               'hostname': 'instance-00001'},
               {'ip_addr': '192.168.96.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003}],
        :param fcp_template_id
        """
        return self._volumeop.volume_refresh_bootmap(fcpchannels, wwpns, lun,
                                                wwid=wwid,
                                                transportfiles=transportfiles,
                                                guest_networks=guest_networks,
                                                fcp_template_id=fcp_template_id)

    def volume_detach(self, connection_info):
        """ Detach a volume from a guest. It's prerequisite to active multipath
            feature on the guest before utilizing persistent volumes.

         :param dict connection_info: A dict comprised of a list of information
               used to establish host-volume connection, including:
               - alias: of type string. A constant valid alias of the volume
               after it being attached onto the guest, i.e. '/dev/vda'. Because
               the system generating device name could change after each
               rebooting, it's necessary to have a constant name to represent
               the volume in its life time.
               - protocol: of type string. The protocol by which the volume is
               connected to the guest. The only one supported now is 'fc' which
               implies FibreChannel.
               - fcps: of type list. The address of the FCP devices used by the
               guest to connect to the volume.
               - wwpns: of type list. The WWPN values through which the volume
               can be accessed, excluding prefixing '0x'.
               - dedicate: of type list. The address of the FCP devices which
               will be undedicated from the guest after removing the volume.
        """
        self._volumeop.detach_volume_from_instance(connection_info)

    @check_guest_exist()
    def guest_create_network_interface(self, userid, os_version,
                                       guest_networks, active=False):
        """ Create network interface(s) for the guest inux system. It will
            create the nic for the guest, add NICDEF record into the user
            direct. It will also construct network interface configuration
            files and punch the files to the guest. These files will take
            effect when initializing and configure guest.

        :param str userid: the user id of the guest
        :param str os_version: operating system version of the guest
        :param list guest_networks: a list of network info for the guest.
               It has one dictionary that contain some of the below keys for
               each network, the format is:
               {'ip_addr': (str) IP address or None,
               'dns_addr': (list) dns addresses or None,
               'gateway_addr': (str) gateway address or None,
               'cidr': (str) cidr format,
               'nic_vdev': (str)nic VDEV, 1- to 4- hexadecimal digits or None,
               'nic_id': (str) nic identifier or None,
               'mac_addr': (str) mac address or None, it is only be used when
               changing the guest's user direct. Format should be
               xx:xx:xx:xx:xx:xx, and x is a hexadecimal digit
               'osa_device': (str) OSA address or None,
               'hostname': (str) Optional. The hostname of the vm.}

               Example for guest_networks:
               [{'ip_addr': '192.168.95.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.95.1',
               'cidr': "192.168.95.0/24",
               'nic_vdev': '1000',
               'mac_addr': '02:00:00:12:34:56',
               'hostname': 'instance-00001'},
               {'ip_addr': '192.168.96.10',
               'dns_addr': ['9.0.2.1', '9.0.3.1'],
               'gateway_addr': '192.168.96.1',
               'cidr': "192.168.96.0/24",
               'nic_vdev': '1003}]
        :param bool active: whether add a nic on active guest system
        :returns: guest_networks list, including nic_vdev for each network
        :rtype: list
        """
        if len(guest_networks) == 0:
            errmsg = ("API guest_create_network_interface: "
                      "Network information is required but not provided")
            raise exception.SDKInvalidInputFormat(msg=errmsg)

        for network in guest_networks:
            vdev = nic_id = mac_addr = ip_addr = OSA = None
            if 'nic_vdev' in network.keys():
                vdev = network['nic_vdev']
            if 'osa_device' in network.keys():
                OSA = network['osa_device']
            if 'nic_id' in network.keys():
                nic_id = network['nic_id']

            if (('mac_addr' in network.keys()) and
                (network['mac_addr'] is not None)):
                mac_addr = network['mac_addr']
                if not zvmutils.valid_mac_addr(mac_addr):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid mac address, format should be "
                              "xx:xx:xx:xx:xx:xx, and x is a hexadecimal "
                              "digit")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('ip_addr' in network.keys()) and
                (network['ip_addr'] is not None)):
                ip_addr = network['ip_addr']
                if not netaddr.valid_ipv4(ip_addr):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid management IP address, it should be "
                              "the value between 0.0.0.0 and 255.255.255.255")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('dns_addr' in network.keys()) and
                (network['dns_addr'] is not None)):
                if not isinstance(network['dns_addr'], list):
                    raise exception.SDKInvalidInputTypes(
                        'guest_config_network',
                        str(list), str(type(network['dns_addr'])))
                for dns in network['dns_addr']:
                    if not netaddr.valid_ipv4(dns):
                        errmsg = ("API guest_create_network_interface: "
                                  "Invalid dns IP address, it should be the "
                                  "value between 0.0.0.0 and 255.255.255.255")
                        raise exception.SDKInvalidInputFormat(msg=errmsg)

            if (('gateway_addr' in network.keys()) and
                (network['gateway_addr'] is not None)):
                if not netaddr.valid_ipv4(
                                    network['gateway_addr']):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid gateway IP address, it should be "
                              "the value between 0.0.0.0 and 255.255.255.255")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)
            if (('cidr' in network.keys()) and
                (network['cidr'] is not None)):
                if not zvmutils.valid_cidr(network['cidr']):
                    errmsg = ("API guest_create_network_interface: "
                              "Invalid CIDR, format should be a.b.c.d/n, and "
                              "a.b.c.d is IP address, n is the value "
                              "between 0-32")
                    raise exception.SDKInvalidInputFormat(msg=errmsg)

            try:
                if OSA is None:
                    used_vdev = self._networkops.create_nic(userid, vdev=vdev,
                                                            nic_id=nic_id,
                                                            mac_addr=mac_addr,
                                                            active=active)
                else:
                    used_vdev = self._networkops.dedicate_OSA(userid, OSA,
                                                              vdev=vdev,
                                                              active=active)
                network['nic_vdev'] = used_vdev
            except exception.SDKBaseException:
                LOG.error(('Failed to create nic on vm %s') % userid)
                raise

        try:
            self._networkops.network_configuration(userid, os_version,
                                                   guest_networks,
                                                   active=active)
        except exception.SDKBaseException:
            LOG.error(('Failed to set network configuration file on vm %s') %
                      userid)
            raise
        return guest_networks

    def guests_get_nic_info(self, userid=None, nic_id=None, vswitch=None):
        """ Retrieve nic information in the network database according to
            the requirements, the nic information will include the guest
            name, nic device number, vswitch name that the nic is coupled
            to, nic identifier and the comments.

        :param str userid: the user id of the vm
        :param str nic_id: nic identifier
        :param str vswitch: the name of the vswitch

        :returns: list describing nic information, format is
                  [
                  (userid, interface, vswitch, nic_id, comments),
                  (userid, interface, vswitch, nic_id, comments)
                  ], such as
                  [
                  ('VM01', '1000', 'xcatvsw2', '1111-2222', None),
                  ('VM02', '2000', 'xcatvsw3', None, None)
                  ]
        :rtype: list
        """
        action = "get nic information"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._networkops.get_nic_info(userid=userid, nic_id=nic_id,
                                                 vswitch=vswitch)

    def vswitch_query(self, vswitch_name):
        """Check the virtual switch status

        :param str vswitch_name: the name of the virtual switch
        :returns: Dictionary describing virtual switch info
        :rtype: dict
        """
        action = "get virtual switch information"
        with zvmutils.log_and_reraise_sdkbase_error(action):
            return self._networkops.vswitch_query(vswitch_name)

    @check_guest_exist()
    def guest_delete_network_interface(self, userid, os_version,
                                       vdev, active=False):
        """ delete the nic and network configuration for the vm

        :param str userid: the user id of the guest
        :param str os_version: operating system version of the guest
        :param str vdev: nic device number, 1- to 4- hexadecimal digits
        :param bool active: whether delete a nic on active guest system
        """
        self._networkops.delete_nic(userid, vdev, active=active)
        self._networkops.delete_network_configuration(userid, os_version,
                                                      vdev, active=active)

    def host_get_ssi_info(self):
        """Get z/VM host SSI information.
        :returns: If current z/VM host is an SSI cluster member,
                  returns a list of SSI cluster info, format is:
                  ['ssi_name = SSI',
                   'ssi_mode = Stable',
                   'ssi_pdr = IAS7CM_on_139E',
                   'cross_system_timeouts = Enabled',
                   'output.ssiInfoCount = 4', '',
                   'member_slot = 1',
                   'member_system_id = BOEIAAS7',
                   'member_state = Joined',
                   'member_pdr_heartbeat = 12/28/2021_05:10:21',
                   'member_received_heartbeat = 12/28/2021_05:10:21',
                   '',
                   'member_slot = 2',
                   'member_system_id = BOEIAAS8',
                   'member_state = Joined',
                   'member_pdr_heartbeat = 12/28/2021_05:10:36',
                   'member_received_heartbeat = 12/28/2021_05:10:36',
                   '']
                  otherwise, return [].
        :rtype: list
        """
        return self._hostops.host_get_ssi_info()
