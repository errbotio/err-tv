from errbot.botplugin import BotPlugin
from errbot.jabberbot import botcmd
from datetime import datetime
import tvdb_api

TVDB_KEY = 'EB10E1EFE69B3AA5'

SHOW_INFO = """{seriesname}

Status: {status}
Network: {network}
Airs: {airs_dayofweek} at {airs_time}
First Aired: {firstaired}
Runtime: {runtime}

Rating: {rating}
Genre: {genre}
CRating: {contentrating}
Actors: {actors}

{overview}"""

EPISODE_INFO = """{seasonnumber:>02}x{episodenumber:>02} - {episodename}

First Aired: {firstaired}
Rating: {rating}
Writer/Director: {writer}/{director}
Guest Stars: {gueststars}

{overview}"""

class TV(BotPlugin):
    """ Shows info about your favorite shows [Bridge to tvdb.com]
    """
    min_err_version = '1.2.0'

    def activate(self):
        self.tvdb = tvdb_api.Tvdb(apikey=TVDB_KEY, banners=True) # heavier stuff
        super(TV, self).activate()

    def deactivate(self):
        del self.tvdb
        super(TV, self).deactivate()

    @botcmd
    def tv_info(self, mess, args):
        """ Shows the info for the given TV show
        ie. !tv info breaking bad
        [from tvrage.com]
        """
        if not args:
            return 'Am I supposed to guess the show?...'
        show = self.tvdb[args]
        self.send(mess.getFrom(), show['banner'], message_type=mess.getType())
        return SHOW_INFO.format(**show.data)

    @botcmd
    def tv_next(self, mess, args):
        """ Shows when to expect the next episode of the given show
        ie. !tv next breaking bad
        """
        if not args:
            return 'Am I supposed to guess the show?...'
        show = self.tvdb[args]
        now = datetime.now().date()
        for snb, season in show.iteritems():
            for enb, episode in season.iteritems():
                fa = episode['firstaired']
                if not fa:
                    continue
                firstaired = datetime.strptime(episode['firstaired'], '%Y-%m-%d').date()
                if firstaired >= now:
                    episode['overview'] = '[ZAPPED BY ANTI-SPOILER !]'
                    days = abs((now - firstaired).days)
                    if days == 0:
                        episode['firstaired'] = 'it\'s today!'
                    else:
                        episode['firstaired'] = 'in %d days' % days
                    return EPISODE_INFO.format(**episode)

        self.send(mess.getFrom(), show['banner'], message_type=mess.getType())
        return SHOW_INFO.format(**show.data)


    @botcmd
    def tv_seasons(self, mess, args):
        """ List the seasons of the given show
        """
        if not args:
            return 'Am I supposed to guess the show?...'
        show = self.tvdb[args]

        return 'List of the seasons:\n' + '\n'.join(['Season %s' % key for key in show.keys()])

    @botcmd(split_args_with=' ')
    def tv_season(self, mess, args):
        """ List the episodes of the season
        ie. !tv season 3 breaking bad
        """
        if len(args) < 2 or not args[0].isdigit():
            return 'the syntax is !tv season # name'

        season_number = int(args[0])
        name = ' '.join(args[1:])
        season = self.tvdb[name][season_number]
        return ('List of the episodes of season %02i:\n' % season_number) + '\n'.join(
            ['%02ix%02i [%s] %s ' % (season_number, episode_number, episode['firstaired'], episode['episodename']) for episode_number, episode in season.iteritems()])

    @botcmd(split_args_with=' ')
    def tv_episode(self, mess, args):
        """ List the episodes of the season
        ie. !tv episode 01x03 breaking bad
        """
        if len(args) < 2:
            return 'the syntax is !tv episode ssxee name'
        sxe = args[0].lower()
        if  sxe.index('x') == -1:
            return 'the episode syntax is ssxee with ss = season and ee = episode'
        season_number, episode_number = args[0].split('x')
        if not season_number.isdigit() or not episode_number.isdigit():
            return 'the episode syntax is ssxee with ss = season and ee = episode'
        season_number, episode_number = int(season_number), int(episode_number)
        name = ' '.join(args[1:])
        show = self.tvdb[name]
        if season_number not in show:
            return 'invalid season number'
        season = show[season_number]
        if episode_number not in season:
            return 'invalid episode number'
        episode = season[episode_number]
        self.send(mess.getFrom(), episode['filename'], message_type=mess.getType())
        return EPISODE_INFO.format(**episode)


