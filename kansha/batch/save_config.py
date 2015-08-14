#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--


from nagare.admin import util, command

class SaveConfig(command.Command):

    desc = 'Create a configuration template for kansha, from the default config into the current folder as kansha.cfg.'

    @staticmethod
    def run(parser, options, args):

        for cfg in args:
            (cfgfile, app, dist, conf) = util.read_application(cfg,
                                                               parser.error)

            infile = open(cfgfile)
            outfile = open('%s.cfg' % conf['application']['name'], 'w')
            outfile.write('datadir = "/path/to/folder"\n\n')
            for line in infile:
                oline = line.replace('$root/data', '$datadir')
                outfile.write(oline)
            infile.close()
            outfile.close()
