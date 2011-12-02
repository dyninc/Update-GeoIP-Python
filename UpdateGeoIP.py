''' 
   An example script which will add a newly created web server into a specified region of our GeoIP setup. First the script will check if the service exists, if not it builds it from scratch (and names it "MyGeoIPService, 
   the name is arbitrary so feel free to change it) if it does exists and are just updating it, it will check if the region exists (in this whatever the region parameter is). If it doesn't exist it will create it, if it does it will simply add 
   the new ip address in as an A record for that region. Also add the zone and fqdn as a GeoIP node if they aren't already there (whats the point of having GeoIP set up if there is nothing taking advantage of it :-p )
   
   The credentials are read out of a configuration file in the same directory named credentials.cfg in the format:
   
   [Dynect]
   user : user_name
   customer : customer_name
   password: password
   
   
   The script has the following usage: "python UpdateGeoIP.py zone fqdn region ip countries"
   
   zone - zone to add GeoIP to if it isn't already (ie: myzone.net)
   fqdn - the fully qualified domain name to add GeoIP to if it isn't already (ie: testgslb.myzone.net)
   region - the region to add the ip address to, this is an arbitrary unique name, if the region exists already it will be updated
   countries - comma seperated list (no spaces) of the 2 letter ISO-3166 country codes of the countries for the region (remember that countries cannot exist in multiple regions)
   ip - the ip address of the server (ie: 1.2.3.4)
   
'''

import sys
import ConfigParser
from DynectDNS import DynectRest

if (len(sys.argv) != 6):
	sys.exit("Incorrect Arguments. \n\nUsage: python UpdateGeoIP.py zone fqdn region ip countries\n") 

config = ConfigParser.ConfigParser()
try:
	config.read('credentials.cfg')
except:
	sys.exit("Error Reading Config file")

dynect = DynectRest()

# Log in
arguments = {
	'customer_name':  config.get('Dynect', 'customer', 'none'),
	'user_name':  config.get('Dynect', 'user', 'none'),  
	'password':  config.get('Dynect', 'password', 'none'),
}

dynect = DynectRest()

response = dynect.execute('/Session/', 'POST', arguments)

if response['status'] != 'success':
	sys.exit("Incorrect credentials")

#this is the arbitrary service name
name = 'MyGeoIPService'

zone =  sys.argv[1]
fqdn =  sys.argv[2]
region =  sys.argv[3]
address = sys.argv[4] 
countries = sys.argv[5]
countryArray = countries.split(',')


# Perform action
response = dynect.execute('/Geo/' + name, 'GET')

#if we ran into an error, lets bail out and report the messages that were returned
if response['status'] != 'success':
	sys.exit("Failed to get GeoIp service: " + response['msgs'][0]['INFO'])

get_reply = response['data']

# see if the service is set up, if it is not, then let's create it from scratch
if not get_reply:
	args = { 'name' :  name, 'groups' : [ {'name' : region, 'countries' : countryArray, 'rdata' : {'a_rdata' : {'address' :  address }}, 'nodes' : [{'zone' : zone, 'fqdn' : fqdn}] } ] }
	response = dynect.execute('/Geo/' + name, 'POST', args)
	
	#if we ran into an error, lets bail out and report the messages that were returned
	if response['status'] != 'success':
		sys.exit("Failed to setup GeoIp service: " + response['msgs'][0]['INFO'])
	
	#if we got here, the service is set up but not active.... let's activate it
	args = { 'activate' :  'true'}
	response = dynect.execute('/Geo/' + name, 'PUT', args)
else:
	#we know we have a service so lets just update it
	
	#first lets get the region to see if it exists
	response = dynect.execute('/GeoRegionGroup/' + name  + '/' + region, 'GET')
			
	get_reply = response['data']
	
	# if the region isn't set up yet, create it with the new ip address
	if not get_reply:
		#create the new region and in the ip address
		args = { 'name' : region, 'countries' : countryArray, 'rdata' : {'a_rdata' : {'address' :  address }} } 	
		response = dynect.execute('/GeoRegionGroup/' + name  + '/' + region, 'POST', args)
				
		#if we ran into an error, bail out and report the messages that were returned
		if response['status'] != 'success':
			sys.exit("Failed to setup GeoRegionGroup: " + response['msgs'][0]['INFO'])
	else:
		#update region and A records
		args = { 'name' : region, 'countries' : countryArray, 'rdata' : {'a_rdata' : {'address' :  address }} } 	
		response = dynect.execute('/GeoRegionGroup/' + name  + '/' + region, 'PUT', args)
				
		#if we ran into an error, bail out and report the messages that were returned
		if response['status'] != 'success':
			sys.exit("Failed to update GeoRegionGroup: " + response['msgs'][0]['INFO'])
			

# Log out, to be polite
dynect.execute('/Session/', 'DELETE')