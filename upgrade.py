#!/bin/python
# create by grayscott for the up or download file
# -*- coding:gb2312 -*-

import os
import sys
import xlrd
import argparse
import paramiko

DEFAULT_USER_NAME  = "root"
DEFAULT_PASSWORD   = "cdqy@663400"
DEFAULT_PORT       = 22

class ssh_proxy:
    def __init__(self, host, password, name="root",port=22):
        '''init ssh client and sftp client'''
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(host,port,name,password)

        self.sftp_client = paramiko.Transport((host,port))
        self.sftp_client.connect(None,name,password)
        print("ssh client init ok")

    def send_cmd(self,cmd):

        if cmd == None:
            print("input command is None")
            return

        stdin, stdout, stderr = self.ssh_client.exec_command(cmd,timeout=2)
        res,err = stdout.read(), stderr.read()

        print("{} results:".format(cmd))
        if res:
            print("result {}".format(res.decode('utf-8')))
        if err:
            print("error {}".format(res.decode('utf-8')))

        return
    def send_file(self, srcfile, dstdir):

        if not os.path.isfile(srcfile):
            print("src file {} not exits".format(srcfile))
            return
        dstfile = dstdir + "/" + os.path.basename(srcfile)
        sftp = paramiko.SFTPClient.from_transport(self.sftp_client)
        sftp.put(srcfile, dstfile)

        print("src file {} dst file {}".format(srcfile, dstfile))
        return

    def get_file(self,srcfile,dstdir):

        sftp = paramiko.SFTPClient.from_transport(self.sftp_client)
        dstfile = dstdir + "/" + os.path.basename(srcfile)

        sftp.get(dstfile, srcfile)

        if not os.path.exists(dstfile):
            print("dstdir {} is not exits download failed".format(dstfile))

        return
    def de_init(self):
        self.sftp_client.close()
        self.ssh_client.close()

class excel_parse:
    def __init__(self, file):
        '''excel should be this pattern host user_name password'''
        if not os.path.exists(file):
            print("file {} is not exits".format(file))
            return
        self.excelfile = xlrd.open_workbook(file)
        self.sheet = self.excelfile.sheet_by_index(0)
        self.raw_index = 0

    def get_ipaddr(self,raw_index):

        if raw_index <= 1 or raw_index > self.sheet.nrows:
            print("the raw index {} is not illegal".format(raw_index))
            return

        return self.sheet.cell_value(raw_index,0).encode('utf-8')

    def get_password(self, raw_index):
        if raw_index <= 1 or raw_index > self.sheet.nrows:
            print("the raw index {} is not illegal".format(raw_index))
            return
        if self.sheet.cell_value(raw_index,2) is None:
            return DEFAULT_PASSWORD
        return self.sheet.cell_value(raw_index,2).encode('utf-8')

    def get_name(self, raw_index):
        if raw_index <= 1 or raw_index > self.sheet.nrows:
            print("the raw index {} is not illegal".format(raw_index))
            return
        if self.sheet.cell_value(raw_index,1) is None:
            return DEFAULT_PASSWORD
        return self.sheet.cell_value(raw_index,1).encode('utf-8')

    def get_port(self, raw_index):
        return DEFAULT_PORT

    def _get_rawlist(self, raw_index):
        if raw_index <= 0 or raw_index > self.sheet.nrows:
            print("the raw index {} is not illegal".format(raw_index))
            return None
        raw_value = self.sheet.row(raw_index)

        temp = [raw_value[0].value, DEFAULT_PORT, raw_value[1].value, raw_value[2].value]
        if temp[2] is None:
            temp[2] = DEFAULT_USER_NAME
        if temp[3] is None:
            temp[3] = DEFAULT_PASSWORD

        return temp
    '''implement for function'''
    def __iter__(self):
        self.raw_index = 1
        return self
    '''iterator next functions'''
    def __next__(self):
        if self.raw_index >= self.sheet.nrows:
            raise StopIteration
        else:
            temp = self._get_rawlist(self.raw_index)
            print("temp is {}".format(temp))
            self.raw_index += 1
            return temp
    def  __getitem__(self, raw_index):
        return self._get_rawlist(raw_index)

class upgrade:
    def __init__(self):
        '''init arguments parser and modify config'''
        self.parser = argparse.ArgumentParser(description="automatic upgrade source file")
        self.parser.add_argument("-f","--uploadfile",metavar="file",action="append",help="giving the upload file")
        self.parser.add_argument("-c", "--config",metavar="config",action="store", help="please giving the config file node list file")
        self.parser.add_argument("-d", "--directory", metavar="dir",action="store", default="/etc/myshell",help="giving up load target directory default is %(default)s")
        self.parser.add_argument("-i", "--instruction", metavar="command",action="store", help='''giving the upload instruction with you self {directory}{nodeip} {0}will replace by real ''')

        if not self._parse_args():
            self._print_help()
            exit(-1)

        print("upgrade init ok")

    def _print_help(self):
        self.parser.print_help()

    def activate_cmd(self):

        for raw in self.excel:
            ssh_session = ssh_proxy(raw[0],raw[3],raw[2],raw[1])
            for file in self.args.uploadfile:
                ssh_session.send_file(os.path.normpath(file),self.args.directory)
            if hasattr(self.args, 'instruction'):
                template = self.args.instruction
                template = template.replace('{directory}',self.args.directory)
                template = template.replace('{nodeip}', raw[0])
                for index in range(len(self.args.uploadfile)):
                    template = template.replace('{'+str(index)+'}', os.path.basename(self.args.uploadfile[index]))

                ssh_session.send_cmd(template)
        return
    def _parse_args(self):
        self.args = self.parser.parse_args()

        if not hasattr(self.args, 'uploadfile'):
            print("the uploadfile file is not exits or input pattern illegal")
            return False

        if not hasattr(self.args, 'directory'):
            print("the directory file is not exits or input pattern illegal")
            return False

        if not hasattr(self.args, 'config'):
            print("the config file is not exits or input pattern illegal")
            return False

        print("upload file {},target directory{},config file{},instruction {}".format(self.args.uploadfile,self.args.directory,self.args.config,self.args.instruction))

        self.excel = excel_parse(os.path.normpath(self.args.config))

        return True

if __name__ == '__main__':
    myupgrade=upgrade()
    myupgrade.activate_cmd()