############################################################
#
# This class aims to control an airconditioner/fan setup
#
# written to be run from AppDaemon for a HASS or HASSIO install
#
# created: 26/12/2020
# 
############################################################

############################################################
# 
# In the apps.yaml file you will need the following
# updated for your database path, stop ids and name of your flag
#
# climatecontrol:
#   module: climatecontrol
#   class: Mangage_Climate
#   fhigh: "sensor.calwell_temp_max_0"
#   flow: "sensor.calwell_temp_min_0"
#   cexttemp: "sensor.tuggeranong_temp"
#   cinttemp: "sensor.inside_now"
#   solarstatus: "input_boolean.power_ready"
#   presenceaway: "input_boolean.presence_away"
#   exthigh: "input_number.cc_exthigh"
#   inthigh: "input_number.cc_inthigh"
#   opthigh: "input_number.cc_opthigh"
#   optlow: "input_number.cc_optlow"
#   intlow: "input_number.cc_intlow"
#   extlow: "input_number.cc_extlow"
#   aircon: "climate.rushbrook_aircon" # climate.lounge # if we want to use it
#   fan: "fan.master_fan,fan.staci_s_fan,fan.delia_s_fan,fan.lounge"
#   manual_override: "input_boolean.cc_ac_manual"
#
############################################################

# import the function libraries
#import requests
#import datetime
#import json
import appdaemon.plugins.hass.hassapi as hass

class Manage_Climate(hass.Hass):

    # the name of the flags in HA to use
    
    FHIGHN = "" # Forecast High
    FLOWN = "" # Forecast Low
    CEXTEMPN = "" # current external temperature
    CINTEMPN = "" # current internal temperature
    SOLARN = "" # Solar status 
    AWAYN = "" # Everyone away?
    MANUAL = "" # Manual override (ignore temp code)

    # these are the names of the sensors
    EXTHIGHN = "" # highest temp we are happy the house to get to ever
    INTHIGHN = "" # highest temp we are happy to live with
    OPTHIGHN = "" # highest temp we would prefer
    OPTLOWN = "" # lowest temp we would prefer
    INTLOWN = "" # lowest temp we are happy to live with
    EXTLOWN = "" # lowest temp we are happy the houe to get to ever

    # these are the values
    EXTHIGH = "" # highest temp we are happy the house to get to ever
    INTHIGH = "" # highest temp we are happy to live with
    OPTHIGH = "" # highest temp we would prefer
    OPTLOW = "" # lowest temp we would prefer
    INTLOW = "" # lowest temp we are happy to live with
    EXTLOW = "" # lowest temp we are happy the houe to get to ever

    FAN = [] # all the fans to control
    AIRCON = [] # all the climate controls we have access to
    
    tick_up_mdi = "mdi:arrow-top-right"
    tick_down_mdi = "mdi:arrow-bottom-left"
    tick_mdi = "mdi:progress-check"

    # run each step against the database
    def initialize(self):

        # get the values from the app.yaml that has the relevant personal settings
        self.FHIGHN = self.args["fhigh"]
        self.FLOWN = self.args["flow"]
        self.CEXTEMPN = self.args["cexttemp"]
        self.CINTEMPN = self.args["cinttemp"]
        self.SOLARN = self.args["solarstatus"]
        self.AWAYN = self.args["presenceaway"]
        self.MANUAL = self.args["manual_override"]
        
        self.EXTHIGHN = self.args["exthigh"]
        self.INTHIGHN = self.args["inthigh"]
        self.OPTHIGHN = self.args["opthigh"]
        self.OPTLOWN = self.args["optlow"]
        self.INTLOWN = self.args["intlow"]
        self.EXTLOWN = self.args["extlow"]

        self.FAN = self.args["fan"].split(",")
        self.AIRCON = self.args["aircon"].split(",")

        # listen to HA for the flag to update the sensor
        # if the forecast high changes, only adjust when the internal temperature changes - don't fiddle with it every second
        #self.listen_state(self.main, self.FHIGHN)
        # if the forecast low changes, only adjust when the internal temperature changes - don't fiddle with it every second
        #self.listen_state(self.main, self.FLOWN)
        # if the solar status changes, only adjust when the internal temperature changes - don't fiddle with it every second
        #self.listen_state(self.main, self.SOLARN)
        # if the external temperature change only adjust when the internal temperature changes - don't fiddle with it every second
        #self.listen_state(self.main, self.CEXTEMPN)

        # if the internal temperature or if everyone leaves, adjust the climate control
        self.listen_state(self.main, self.CINTEMPN)
        self.listen_state(self.main, self.AWAYN)
        # if set to manual, then ignore everything
        self.listen_state(self.ignorer, self.MANUAL)

        # if the user temperature settings change update them on the fly
        self.listen_state(self.setvals, self.EXTHIGHN)
        self.listen_state(self.setvals, self.INTHIGHN)
        self.listen_state(self.setvals, self.OPTHIGHN)
        self.listen_state(self.setvals, self.OPTLOWN)
        self.listen_state(self.setvals, self.INTLOWN)
        self.listen_state(self.setvals, self.EXTLOWN)

        # set the orignal values
        self.load()


    def ignorer(self, entity, attribute, old, new, kwargs):
        """ this watches the ignore flag, to show we are in 'manual mode'
            
        """
        if new == 'on':
            self.log("Manual Mode: ignoring temperature controls")
        else:
            self.log("Controlled Mode: managing temperature controls")



    # run the app
    def main(self, entity, attribute, old, new, kwargs):
        """ this does all the checking and controls the climate
            
        """
        
        if self.get_state(self.MANUAL) != 'on':

            self.log("entity change: " + entity + " old: " + old + " new: " + new)
            logger = ""

            # if the house goes to everyone away - turn everything off now
            if entity == self.AWAYN:
                if new == "on":
                    for ac in self.AIRCON:
                        self.toff(ac, "AC")
                    for fan in self.FAN:
                        self.toff(fan, "FAN")
            # when the internal temperature changes
            elif entity == self.CINTEMPN:
                if new > self.EXTHIGH:
                    # never let it get this hot ever # ensure the house never gets above the set user external high
                    for ac in self.AIRCON:
                        self.ton(ac, "AC", mode="cool", temp=self.EXTHIGH, spd="High")
                    for fan in self.FAN:
                        self.ton(fan, "FAN")
                elif new < self.EXTLOW:
                    #never let it get this cold ever
                    for ac in self.AIRCON:
                        self.ton(ac, "AC", mode="heat", temp=self.EXTLOW, spd="High")
                    for fan in self.FAN:
                        self.toff(fan, "FAN")
                elif new > self.OPTLOW and new < self.INTHIGH:
                    # this is in the goldilocks range, mostly aim to control
                    if self.get_state(self.AWAYN) != 'on': 
                        if self.get_state(self.CEXTEMPN) > self.OPTHIGH:
                            # if the outside temperature is higher than the optimal high (but we are in the goldilocks range)
                            for ac in self.AIRCON:
                                self.ton(ac, "AC", mode="fan_only")
                            for fan in self.FAN:
                                self.ton(fan, "FAN")
                        else:
                            # if the outside temp is lower than optimal but the forecast is higher (but we are in the goldilocks range)
                            if self.get_state(self.FHIGHN) > self.OPTHIGH:
                                for ac in self.AIRCON:
                                    self.toff(ac, "AC")
                                for fan in self.FAN:
                                    self.ton(fan, "FAN")
                            else:
                                # everything is optimal - everything off
                                for ac in self.AIRCON:
                                    self.toff(ac, "AC")
                                for fan in self.FAN:
                                    self.toff(fan, "FAN")
                else:
                    # this is in the outer ranges, need to check more complexity
                    # is the house empty
                    if self.get_state(self.AWAYN) == 'on': 
                        # then in this range just turn off
                        for ac in self.AIRCON:
                            self.toff(ac, "AC")
                        for fan in self.FAN:
                            self.toff(fan, "FAN")
                    else:
                        # people are home, so lets work out how to bring it back to optimal
                        if self.get_state(self.FHIGHN) >= self.INTHIGH:
                            # if the forecast is for high today, then we are cooling
                            # see if we have solar
                            if self.get_state(self.SOLARN) == 'on':
                                # solar is available - cool further
                                if self.get_state(self.CINTEMPN) > self.OPTHIGH:
                                    # internal temp is higher than optimal
                                    for ac in self.AIRCON:
                                        self.ton(ac, "AC", mode="cool", temp=self.OPTHIGH, spd="Low")
                                    for fan in self.FAN:
                                        self.ton(fan, "FAN")
                                else:
                                    # internal temp is not high but
                                    # external temp is high
                                    if self.get_state(self.CEXTEMPN) > self.OPTHIGH:
                                        for ac in self.AIRCON:
                                            self.ton(ac, "AC", mode="fan_only")
                                        for fan in self.FAN:
                                            self.ton(fan, "FAN")
                                    else:
                                        # external temp is ok, let it naturally cool
                                        for ac in self.AIRCON:
                                            self.toff(ac, "AC")
                                        for fan in self.FAN:
                                            self.toff(fan, "FAN")
                            else:
                                # solar is not available - some cooling
                                if self.get_state(self.CINTEMPN) > self.INTHIGH:
                                    # internal temp is higher than optimal
                                    for ac in self.AIRCON:
                                        self.ton(ac, "AC", mode="cool", temp=self.INTHIGH, spd="Mid")
                                    for fan in self.FAN:
                                        self.ton(fan, "FAN")
                                else:
                                    # internal temp is not high but
                                    # external temp is high
                                    if self.get_state(self.CEXTEMPN) > self.OPTHIGH:
                                        for ac in self.AIRCON:
                                            self.ton(ac, "AC", mode="fan_only")
                                        for fan in self.FAN:
                                            self.ton(fan, "FAN")
                                    else:
                                        # external temp is ok, let it naturally cool
                                        for ac in self.AIRCON:
                                            self.toff(ac, "AC")
                                        for fan in self.FAN:
                                            self.toff(fan, "FAN") 

                        elif self.get_state(self.FHIGHN) <= self.OPTLOW:
                            # if the forecast is for low today, then we are heating
                            # see if we have solar
                            if self.get_state(self.SOLARN) == 'on':
                                # solar is available - heat further
                                if self.get_state(self.CINTEMPN) < self.OPTLOW:
                                    # internal temp is higher than optimal
                                    for ac in self.AIRCON:
                                        self.ton(ac, "AC", mode="heat", temp=self.OPTLOW, spd="Low")
                                    for fan in self.FAN:
                                        self.toff(fan, "FAN")
                                else:
                                    # internal temp is fine
                                    for ac in self.AIRCON:
                                        self.toff(ac, "AC")
                                    for fan in self.FAN:
                                        self.toff(fan, "FAN")
                            else:
                                # solar is not available - some cooling
                                if self.get_state(self.CINTEMPN) < self.INTLOW:
                                    # internal temp is higher than optimal
                                    for ac in self.AIRCON:
                                        self.ton(ac, "AC", mode="heat", temp=self.INTLOW, spd="Mid")
                                    for fan in self.FAN:
                                        self.toff(fan, "FAN")
                                else:
                                    # internal temp is ok
                                    # external temp is ok, let it naturally cool
                                    for ac in self.AIRCON:
                                        self.toff(ac, "AC")
                                    for fan in self.FAN:
                                        self.toff(fan, "FAN")
                        else:
                            # if the forecast is in the middle then we do nothing? and let the house cool or heat naturally?
                            pass

            self.log(logger)



    def setvals(self, entity, attribute, old, new, kwargs):
        """ this sets the user values that are used to control the climate
        """

        if entity == self.EXTHIGHN:
            self.EXTHIGH = new
            self.log("Change Maximum External High to " + new)
        elif entity == self.INTHIGHN:
            self.INTHIGH = new
            self.log("Change Internal High to " + new)
        elif entity == self.OPTHIGHN:
            self.OPTHIGH = new
            self.log("Change Optimal High to " + new)
        elif entity == self.OPTLOWN:
            self.OPTLOW = new
            self.log("Change Optimal Low to " + new)
        elif entity == self.INTLOWN:
            self.INTLOW = new
            self.log("Change Internal Low to " + new)
        elif entity == self.EXTLOWN:
            self.EXTLOW = new
            self.log("Change Maximum Low to " + new)
        else:
            self.log("Unknown User Value Change Requested")


    def load(self):
        """ this sets the original user values that are used to control the climate
        """
        self.EXTHIGH = self.get_state(self.EXTHIGHN)
        self.INTHIGH = self.get_state(self.INTHIGHN)
        self.OPTHIGH = self.get_state(self.OPTHIGHN)
        self.OPTLOW = self.get_state(self.OPTLOWN)
        self.INTLOW = self.get_state(self.INTLOWN)
        self.EXTLOW = self.get_state(self.EXTLOWN)
        self.log("Set all original User Values")

    
    def toff(self, unit, aftype):
        """ this will turn off an ac or a fan if it isn't already off
        """

        if self.get_state(unit) != 'off':
            if aftype == "AC":
                self.call_service("climate/turn_off", entity_id=unit)
                self.log(unit + " off")
            elif aftype == "FAN":
                self.call_service("fan/turn_off", entity_id=unit)
                self.log(unit + " off")
            else:
                self.log("unknown off call")
        else:
            self.log("already off - not turning off " + unit)

    
    def ton(self, unit, aftype, mode="fan_only", temp="0.0", spd="Low"):
        """ this will turn on an ac or a fan if it isn't already on
        """

        #if already on, this will set from fan to cool/heat and from cool/heat back to fan
        if float(temp) > 0.0:
            #switch from fan_only to aircon
            if self.get_state(unit) == 'fan_only' and mode != 'fan_only':
                self.call_service("climate/set_hvac_mode", entity_id=unit, hvac_mode=mode)
                self.call_service("climate/set_fan_mode", entity_id=unit, fan_mode=spd)
                self.call_service("climate/set_temperature", entity_id=unit, temperature=temp)
                self.lightwarn()
                self.log(unit + " on to " + mode + " at " + temp)
            #switch from aircon to fan_only 
            elif mode == 'fan_only' and self.get_state(unit) != 'fan_only':
                self.call_service("climate/set_hvac_mode", entity_id=unit, hvac_mode=mode)
                self.call_service("climate/set_fan_mode", entity_id=unit, fan_mode=spd)
                self.call_service("climate/set_temperature", entity_id=unit, temperature=temp)
                self.log(unit + " on to " + mode)
            #switch temperatures when using aircon
            elif self.get_state(unit) != 'fan_only' and self.get_state(unit, attribute='temperature') != temp:
                self.call_service("climate/set_temperature", entity_id=unit, temperature=temp)
                self.log(unit + " on to " + mode + " at " + temp)

        if self.get_state(unit) == 'off':
            if aftype == "AC":
                    self.call_service("climate/set_hvac_mode", entity_id=unit, hvac_mode=mode)
                    self.call_service("climate/set_fan_mode", entity_id=unit, fan_mode=spd)
                    self.call_service("climate/set_temperature", entity_id=unit, temperature=temp)
                    self.call_service("climate/turn_on", entity_id=unit)
                    if self.get_state(mode) == 'fan_only':
                        self.lightwarn()
                    self.log(unit + " on to " + mode)
            elif aftype == "FAN":
                self.call_service("fan/turn_on", entity_id=unit)
                self.log(unit + " on")
            else:
                self.log("unknown on call")
        else:
            self.log("already on - not turning on " + unit)

    
    ## THIS WOULD NEED TO BE GENERICISED IF MADE AVAILABLE TO COMMUNITY

    def lightwarn(self):
        """ this will flash the front hall light if the doors are open when the aircon kicks in
        """

        if self.get_state("binary_sensor.fdoor_open") == 'on' or self.get_state("binary_sensor.bdoor_open") == 'on':
            self.call_service("light/turn_on", entity_id="light.front_hall", brightness=100)
            