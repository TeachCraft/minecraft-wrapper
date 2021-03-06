
**< class Player(object) >**

    .. code:: python

        def __init__(self, username, wrapper)

    ..

    This class is normally passed as an argument to an event
    callback, but can be also be called using getPlayer(username):

    .. code:: python

        player = self.api.getPlayer(<username>)

    ..

    Player objects contains methods and data of a currently
    logged-in player. This object is destroyed
    upon logging off.  Most features are tied heavily to
    proxy mode implementations and the proxy client instance.

    

-  execute(self, string)

        Run a command as this player. If proxy mode is not enabled,
        it simply falls back to using the 1.8 'execute' command. To 
        be clear, this does NOT work with any Wrapper.py or plugin 
        commands.  The command does not pass through the wrapper.  
        It is only sent to the server console.

        :arg string: full command string send on player's behalf to server.

        :returns: Nothing; passes the server or the console as an
         "execute" command.

        

-  sendCommand(self, command, args)

        Sends a command to the wrapper interface as the player instance.
        This would find a nice application with a '\sudo' plugin command.

        :sample usage:

            .. code:: python

                player=getPlayer("username")
                player.sendCommand("perms", ("users", "SurestTexas00", "info"))

            ..

        :Args:
            :command: The wrapper (or plugin) command to execute; no
             slash prefix
            :args: list of arguments (I think it is a list, not a
             tuple or dict!)

        :returns: Nothing; passes command through commands.py function
         'playercommand()'

        

-  say(self, string)

        Send a message as a player.

        :arg string: message/command sent to the server as the player.

        Beware: *in proxy mode, the message string is sent directly to*
        *the server without wrapper filtering,so it could be used to*
        *execute minecraft commands as the player if the string is*
        *prefixed with a slash.*

        

-  getClient(self)

        Returns the player client context.  Use at your own risk - items
        in client are generally private or subject to change (you are
        working with an undefined API!)... what works in this wrapper
        version may not work in the next.

        :returns: player client object

        

-  getPosition(self)

        Get the players position
        
        :Note:  The player's position is obtained by parsing client
         packets, which are not sent until the client logs in to 
         the server.  Allow some time after server login to verify 
         the wrapper has had the oppportunity to parse a suitable 
         packet to get the information!
        
        :returns: a tuple of the player's current position x, y, z, 
         and yaw, pitch of head.
        
        

-  getGamemode(self)

        Get the player's current gamemode.
        
        :Note:  The player's Gamemode is obtained by parsing client
         packets, which are not sent until the client logs in to 
         the server.  Allow some time after server login to verify 
         the wrapper has had the oppportunity to parse a suitable 
         packet to get the information!
         
        :returns:  An Integer of the the player's current gamemode.

        

-  getDimension(self)

        Get the player's current dimension.

        :Note:  The player's Dimension is obtained by parsing client
         packets, which are not sent until the client logs in to 
         the server.  Allow some time after server login to verify 
         the wrapper has had the oppportunity to parse a suitable 
         packet to get the information!
         
         :returns: the player's current dimension.

             :Nether: -1
             :Overworld: 0
             :End: 1

        

-  setGamemode(self, gamemode=0)

        Sets the user's gamemode.

        :arg gamemode: desired gamemode, as a value 0-3

        

-  setResourcePack(self, url, hashrp="")

        Sets the player's resource pack to a different URL. If the
        user hasn't already allowed resource packs, the user will
        be prompted to change to the specified resource pack.
        Probably broken right now.

        :Args:
            :url: URL of resource pack
            :hashrp: resource pack hash

        

-  isOp(self, strict=False)

        Check if player has Operator status. Accepts player as OP
        based on either the username OR server UUID (unless 'strict'
        is set).

        Note: *If a player has been opped since the last server start,*
        *make sure that you run refreshOpsList() to ensure that*
        *wrapper will acknowlege them as OP.*

        :arg strict: True - use ONLY the UUID as verification

        :returns:  A 1-10 (or more?) op level if the player is currently
         a server operator.

        Can be treated, as before, like a
        boolean - 'if player.isOp():', but now also adds ability
        to granularize with the OP level.  Levels above 4 are
        reserved for wrapper.  10 indicates owner. 5-9 are
        reserved for future minecraft or wrapper levels.  pre-1.8
        servers return 1.  levels above 4 are based on name only
        from the file "superops.txt" in the wrapper folder.
        To assign levels, change the lines of <PlayerName>=<oplevel>
        to your desired names.  Player must be an actual OP before
        the superops.txt will have any effect.  Op level of 10 is
        be required to operate permissions commands.

        

-  message(self, message="")

        Sends a message to the player.

        :arg message: Can be text, colorcoded text, or json chat

        

-  setVisualXP(self, progress, level, total)

         Change the XP bar on the client's side only. Does not
         affect actual XP levels.

        :Args:
            :progress:  Float between Between 0 and 1
            :level:  Integer (short in older versions) of EXP level
            :total: Total EXP.

        :returns: Nothing

        

-  openWindow(self, windowtype, title, slots)

        Opens an inventory window on the client side.  EntityHorse
        is not supported due to further EID requirement.  *1.8*
        *experimental only.*

        :Args:
            :windowtype:  Window Type (text string). See below
             or applicable wiki entry (for version specific info)
            :title: Window title - wiki says chat object (could
             be string too?)
            :slots:

        :returns: None (False if client is less than 1.8 version)


        Valid window names (1.9)

        :minecraft\:chest: Chest, large chest, or minecart with chest

        :minecraft\:crafting_table: Crafting table

        :minecraft\:furnace: Furnace

        :minecraft\:dispenser: Dispenser

        :minecraft\:enchanting_table: Enchantment table

        :minecraft\:brewing_stand: Brewing stand

        :minecraft\:villager: Villager

        :minecraft\:beacon: Beacon

        :minecraft\:anvil: Anvil

        :minecraft\:hopper: Hopper or minecart with hopper

        :minecraft\:dropper: Dropper

        :EntityHorse: Horse, donkey, or mule

        

-  setPlayerAbilities(self, fly)

        *based on old playerSetFly (which was an unfinished function)*

        NOTE - You are implementing these abilities on the client
         side only.. if the player is in survival mode, the server
         may think the client is hacking!

        this will set 'is flying' and 'can fly' to true for the player.
        these flags/settings will be set according to the players
        properties, which you can set just prior to calling this
        method:

            :getPlayer().godmode:  Hex or integer (see chart below)

            :getPlayer().creative: Hex or integer (see chart below)

            :getPlayer().field_of_view: Float - default is 1.0

            :getPlayer().fly_speed: Float - default is 1.0

        :arg fly: Boolean

            :True: set fly mode.
            :False: to unset fly mode

        :Bitflags used (for all versions): These can be added to
         produce combination effects.   This function sets
         0x02 and 0x04 together (0x06).

            :Invulnerable: 0x01
            :Flying: 0x02
            :Allow Flying: 0x04
            :Creative Mode: 0x08

        :returns: Nothing

        

-  sendBlock(self, position, blockid, blockdata, sendblock=True,
                  numparticles=1, partdata=1)

        Used to make phantom blocks visible ONLY to the client.  Sends
        either a particle or a block to the minecraft player's client.
        For blocks iddata is just block id - No need to bitwise the
        blockdata; just pass the additional block data.  The particle
        sender is only a basic version and is not intended to do
        anything more than send something like a barrier particle to
        temporarily highlight something for the player.  Fancy particle
        operations should be custom done by the plugin or someone can
        write a nicer particle-renderer.

        :Args:

            :position: players position as tuple.  The coordinates must
             be in the player's render distance or the block will appear
             at odd places.

            :blockid: usually block id, but could be particle id too.  If
             sending pre-1.8 particles this is a string not a number...
             the valid values are found here

            :blockdata: additional block meta (a number specifying a subtype).

            :sendblock: True for sending a block.

            :numparticles: if particles, their numeric count.

            :partdata: if particles; particle data.  Particles with
             additional ID cannot be used ("Ironcrack").

        :Valid 'blockid' values:
         http://wayback.archive.org/web/20151023030926/https://gist.github.com/thinkofdeath/5110835

        

-  getItemInSlot(self, slot)

        Returns the item object of an item currently being held.

        

-  getHeldItem(self)

        Returns the item object of an item currently being held.

        

-  hasPermission(self, node, another_player=False, group_match=True, find_child_groups=True)

        If the player has the specified permission node (either
        directly, or inherited from a group that the player is in),
        it will return the value (usually True) of the node.
        Otherwise, it returns False.  Using group_match and
        find_child_groups are enabled by default.  Permissions
        can be sped up by disabling child inheritance or even
        group matching entirely (for high speed loops, for
        instance).  Normally, permissions are related to
        commands the player typed, so the 'cost' of child
        inheritance is not a concern.

        :Args:
            :node: Permission node (string)
            :another_player: sending a string name of another player
             will check THAT PLAYER's permission instead! Useful for
             checking a player's permission for someone who is not
             logged in and has no player object.
            :group_match: return a permission for any group the player
             is a member of.  If False, will only return permissions
             player has directly.
            :find_child_groups: If group matching, this will
             additionally locate matches when a group contains
             a permission that is another group's name.  So if group
             'admin' contains a permission called 'moderator', anyone
             with group admin will also have group moderator's
             permissions as well.

        :returns:  Boolean indicating whether player has permission or not.

        

-  setPermission(self, node, value=True)

        Adds the specified permission node and optionally a value
        to the player.

        :Args:
            :node: Permission node (string)
            :value: defaults to True, but can be set to False to
             explicitly revoke a particular permission from the
             player, or to any arbitrary value.

        :returns: Nothing

        

-  removePermission(self, node)

        Completely removes a permission node from the player. They
        will inherit this permission from their groups or from
        plugin defaults.

        If the player does not have the specific permission, an
        IndexError is raised. Note that this method has no effect
        on nodes inherited from groups or plugin defaults.

        :arg node: Permission node (string)

        :returns:  Boolean; True if operation succeeds, False if
         it fails (set debug mode to see/log error).

        

-  hasGroup(self, group)

        Returns a boolean of whether or not the player is in
        the specified permission group.

        :arg group: Group node (string)

        :returns:  Boolean of whether player has permission or not.

        

-  getGroups(self)

        Returns a list of permission groups that the player is in.

        :returns:  list of groups

        

-  setGroup(self, group, creategroup=True)

        Adds the player to a specified group.  Returns False if
        the command fails (set debiug to see error).  Failure
        is only normally expected if the group does not exist
        and creategroup is False.

        :Args:
            :group: Group node (string)
            :creategroup: If True (by default), will create the
             group if it does not exist already.  This WILL
             generate a warning log since it is not an expected
             condition.

        :returns:  Boolean; True if operation succeeds, False
         if it fails (set debug mode to see/log error).

        

-  removeGroup(self, group)

        Removes the player to a specified group.

        :arg group: Group node (string)

        :returns:  (use debug logging to see any errors)

            :True: Group was found and .remove operation performed
             (assume success if no exception raised).
            :None: User not in group
            :False: player uuid not found!

        

-  getFirstLogin(self)

        Returns a tuple containing the timestamp of when the user
        first logged in for the first time, and the timezone (same
        as time.tzname).

        

-  connect(self, address, port)

        Upon calling, the player object will become defunct and
        the client will be transferred to another server or wrapper
        instance (provided it has online-mode turned off).

        :Args:
            :address: server address (local address)
            :port: server port (local port)

        :returns: Nothing

        
