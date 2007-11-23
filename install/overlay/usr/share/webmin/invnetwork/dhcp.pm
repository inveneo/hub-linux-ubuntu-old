
use constant RESOLVE_CONF => "/etc/resolv.conf";
use constant INTERFACES_CONF => "/etc/network/interfaces";

sub get_dhcp_status {
    
    local( $/ );

    system("/etc/init.d/samba-shares.sh start");

    open(STATUS, "/etc/init.d/dhcp3-server status |");
    $result = <STATUS>;
    close(STATUS);
    
    return ( $result =~ m/not running/ ) ? "Disabled" : "Enabled";

}

sub get_interface_info {
	local ($target_iface) = shift;
	local %retval;

	# retrieve interface information from INTERFACES_CONF file
	open(FH, INTERFACES_CONF);
	local $in_iface=0;
	foreach $line ( <FH> ) { 		
		if ( $line =~ m/^\s*iface\s*(\w+)/ ) {
			$iface = $1;
			if ( $iface eq $target_iface ) {
				$in_iface=1;
			}			
		} elsif ( $line =~ m/^\s*((mapping)|(allow)|(auto))/ ) {
			$in_iface=0;
	  	} elsif ( $in_iface ) {
			if ( $line =~ m/^\s*([\w-]*)\s*(.*)\s*$/ ) {
				$retval{$1} = $2;					
			}
		}
	} 
	close(FH);
	

	# retrieve nameserver information from RESOLVE_CONF file.	
	open(FH, RESOLVE_CONF);
	foreach $line ( <FH> ) {
		if ($line =~ m/nameserver\s*(.+)\s*$/) {
			local $server = $1;
			local $dnslist = $retval{'dns'};
			if ( $dnslist ) {
				push @{ $dnslist }, $server;
			} else {
				$dnslist = [ $server ];
				$retval{'dns'} = $dnslist;			
			}			
		}
	}	
	close(FH);

	return %retval;

}

sub find_member { 
	my ( $host, $memberName ) = @_;

	my ( $members ) = ${ $host }{'members'};
	
	foreach $member ( @{$members} ) {	
		
		$name = ${ $member }{'name'};
		
		if ( lc($name) eq lc($memberName) ) {
			$value = ${ $member }{'text'};		
			return $value;
		}

	}

	return undef;

}

1;