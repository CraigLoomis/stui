# 01/25/2012  change motor position description to resovle a conflict of data types ?? 
# 02/12/2013 EM: calculate TAI time for new stui version 
# 04/15/2013 EM:  
#  1) updates self.updateFunSos[1,2] functions: no compare with previous velues
#  2) set callNow=False for these sps functions; 
#  3) boss.motorPosition forced to update after sos update; 
#  4) added mcp.gang position changes


import RO.Wdg
import TUI.Models
import time
#import Tkinter
import RO.Astro.Tm

encl="";  loadCart=""; gtfState=""; gtfStages=""
gStat="";  gexpTime=""; guiderCorr=""
calState=""; sciState=""
expState=""

class ScriptClass(object):
    def __init__(self, sr):
        self.sr = sr
        sr.master.winfo_toplevel().wm_resizable(True, True)

        self.name="logFun, ver04/15/2013"
        print "self.name=",self.name
        print  self.name, "current date=", self.getTAITimeStrDate()
        
        width=45
        self.redWarn=RO.Constants.sevError
        self.logWdg = RO.Wdg.LogWdg(master=sr.master,width=width, height =22,)
        self.logWdg.grid(row=0, column=0, sticky="news")
        sr.master.rowconfigure(0, weight=1)
        sr.master.columnconfigure(0, weight=1)
        self.logWdg.text.tag_config("v", foreground="darkviolet")
        self.logWdg.text.tag_config("a", foreground="darkgreen") 
        
        self.guiderModel = TUI.Models.getModel("guider")
        self.sopModel = TUI.Models.getModel("sop")
        self.sosModel = TUI.Models.getModel("sos")
        self.apoModel = TUI.Models.getModel("apo")
        self.bossModel = TUI.Models.getModel("boss")
        self.mcpModel = TUI.Models.getModel("mcp")
        self.apogeeModel = TUI.Models.getModel("apogee")

        ss="-- Init --   (%s)"%self.name
        self.logWdg.addMsg(ss)
        print self.name, self.getTAITimeStr(), ss 

        self.apoModel.encl25m.addCallback(self.updateEncl,callNow=True)
        self.guiderModel.cartridgeLoaded.addCallback(self.updateLoadCart,callNow=True)
        self.guiderModel.guideState.addCallback(self.updateGstate, callNow=True)
        self.guiderModel.expTime.addCallback(self.updateGexptime,callNow=True)
        self.guiderModel.guideEnable.addCallback(self.guideCorrFun,callNow=True)

        self.sopModel.gotoFieldState.addCallback(self.updateGtfStateFun,callNow=False)
      #  self.sopModel.gotoFieldStages.addCallback(self.updateGtfStagesFun,callNow=True)
      #  self.sopModel.doCalibsState.addCallback(self.updateCalStateFun,callNow=True)
      #  self.sopModel.doScienceState.addCallback(self.updateSciStateFun,callNow=True) 
        
        self.sp1Res=self.sosModel.sp1Residuals[0:3]
        self.sp2Res=self.sosModel.sp2Residuals[0:3]        
        self.sosModel.sp1Residuals.addCallback(self.updateFunSos1,callNow=False)
        self.sosModel.sp2Residuals.addCallback(self.updateFunSos2,callNow=False)

        self.bossModel.exposureState.addCallback(self.updateBossState,callNow=True)
        
        self.motPos=self.bossModel.motorPosition[:]
        self.sp1ToUpdate=False
        self.sp2ToUpdate=False        
     #   self.motPos=[0,0,0,0,0,0]
     #   for i in range(0,6):
     #       self.motPos[i]=sr.getKeyVar(self.bossModel.motorPosition, ind=i,  defVal=0)
        self.bossModel.motorPosition.addCallback(self.motorPosition,callNow=True)

        self.sp1move=sr.getKeyVar(self.sosModel.sp1AverageMove, ind=0, defVal=0)
        self.sp2move=sr.getKeyVar(self.sosModel.sp2AverageMove, ind=0, defVal=0)
        self.sosModel.sp1AverageMove.addCallback(self.sp1AverageMove,callNow=False)
        self.sosModel.sp2AverageMove.addCallback(self.sp2AverageMove,callNow=False)

        #mcp        
     #   self.FFs=self.mcpModel.ffsStatus[:]
        self.FFs=["","","","","",""]
        self.FFlamp=self.mcpModel.ffLamp[:]
        self.hgCdLamp=self.mcpModel.hgCdLamp[:]
        self.neLamp=self.mcpModel.neLamp[:]        
        self.mcpModel.ffsStatus.addCallback(self.updateFFS,callNow=True)
        self.mcpModel.ffLamp.addCallback(self.updateFFlamp,callNow=True)
        self.mcpModel.hgCdLamp.addCallback(self.updateHgCdLamp,callNow=True)
        self.mcpModel.neLamp.addCallback(self.updateNeLamp,callNow=True)

        #self.apogeeState=self.apogeeModel.exposureWroteSummary[0]
        self.apogeeState=""
        self.apogeeModel.exposureWroteSummary.addCallback(self.updateApogeeExpos, callNow=True)

        self.ngang=""
        self.updateMCPGang(self.mcpModel.apogeeGang[0])
        self.mcpModel.apogeeGang.addCallback(self.updateMCPGang, callNow=True)

        ss= "---- Monitoring ---"
        self.logWdg.addMsg(ss)
        print self.name, self.getTAITimeStr(), ss

    def updateMCPGang(self, keyVar): 
#       if not keyVar.isGenuine: return
       if keyVar[0] != self.ngang: 
           self.ngang=keyVar[0]
           timeStr = self.getTAITimeStr()
           labelHelp=["Disconnected", "Podium", "Cart", "Sparse cals"]
           ss="%s  mcp.gang=%s  (%s)" % (timeStr, self.ngang, labelHelp[int(self.ngang)])
           self.logWdg.addMsg("%s" % (ss))
           print self.name, ss       
        
    def updateApogeeExpos(self, keyVar): 
        if not keyVar.isGenuine: return
        if keyVar[0] != self.apogeeState:
            timeStr = self.getTAITimeStr()
            self.apogeeState=keyVar[0]
            dd0=self.apogeeModel.utrReadState[0]
            dd3=self.apogeeModel.utrReadState[3]
            dth=self.apogeeModel.ditherPosition[1]
            exptp=self.apogeeModel.exposureState[1]
            ss="%s  apogee.expose=%s, %s, %s, %s" % (timeStr, dd0,dd3, dth, exptp)
            self.logWdg.addMsg("%s" % (ss),tags="a")
        
    def motorPosition(self,keyVar):
        if not keyVar.isGenuine: return
        timeStr = self.getTAITimeStr()
        mm=keyVar[:]
        mm1=self.motPos
        if (mm[0]!=mm1[0]) or (mm[1]!=mm1[1]) or (mm[2]!=mm1[2]) or (self.sp1ToUpdate):
                print self.name, "sp1.motor.old=", self.motPos[0],self.motPos[1],self.motPos[2]
                print self.name, "sp1.motor.new=", mm[0],mm[1],mm[2]
                print self.name, "sp1.motor.move=", mm[0]-self.motPos[0], mm[1]-self.motPos[1], mm[2]-self.motPos[2]
                ss1="%s  motorPos.sp1.move:" % (timeStr)
                sp1move=ss1+" %6i,  %6i,  %6i;  " % (mm[0]-self.motPos[0], mm[1]-self.motPos[1],mm[2]-self.motPos[2])
                self.logWdg.addMsg("%s" % (sp1move),tags="v")
                self.sp1ToUpdate=False
        if (mm[3]!=mm1[3]) or (mm[4]!=mm1[4]) or (mm[5]!=mm1[5]) or (self.sp2ToUpdate):      
                print self.name, "sp2.motor.old=", self.motPos[3],self.motPos[4],self.motPos[5]
                print self.name, "sp2.motor.new=", mm[3],mm[4],mm[5]
                print self.name, "sp2.motor.move=", mm[3]-self.motPos[3], mm[4]-self.motPos[4], mm[5]-self.motPos[5]
                ss2="%s  motorPos.sp2.move:" % (timeStr)
                sp2move=ss2+" %6i,  %6i,  %6i;  " % (mm[3]-self.motPos[3], mm[4]-self.motPos[4],mm[5]-self.motPos[5])
                self.logWdg.addMsg("%s" % (sp2move),tags="v")
                self.sp2ToUpdate=False
        self.motPos=mm
        
#    boss mechStatus  -- Parse the status of each conected mech and report it in keyword form.
#    boss moveColl <spec> [<a>] [<b>] [<c>] -- Adjust the position of the colimator motors.
#    boss moveColl spec=sp1 piston=5 
                                       
    def sp1AverageMove(self,keyVar):
        if not keyVar.isGenuine: return
    #    if keyVar[0] == self.sp1move:   return
        timeStr = self.getTAITimeStr()
        ss="%s  sos.sp1AverageMove = %s" % (timeStr, keyVar[0])
        self.logWdg.addMsg("%s" % (ss),tags="a")
        print self.name, ss
        self.sp1move=keyVar[0]
        self.sp1ToUpdate=True

    def sp2AverageMove(self,keyVar):
        if not keyVar.isGenuine: return
#        if keyVar[0] == self.sp2move: return  
        timeStr = self.getTAITimeStr()
        ss="%s  sos.sp2AverageMove = %s" % (timeStr, keyVar[0])
        self.logWdg.addMsg("%s" % (ss),tags="a")
        print self.name, ss
        self.sp2move=keyVar[0]
        self.sp2ToUpdate=True 

    def getTAITimeStr(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%H:%M:%S", currTAITuple) 
      return self.taiTimeStr
      
    def getTAITimeStrDate(self,):
      currPythonSeconds = RO.Astro.Tm.getCurrPySec()
      currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
      self.taiTimeStr = time.strftime("%M:%D:%Y,  %H:%M:%S", currTAITuple) 
      return self.taiTimeStr   

    def updateBossState(self,keyVar):
        if not keyVar.isGenuine: return
        timeStr = self.getTAITimeStr()
        global expState
        if keyVar[0] != expState:
          expTime =keyVar[1]
          expId=int(self.bossModel.exposureId[0])+2
          self.logWdg.text.tag_config("b", foreground="darkblue")
          self.logWdg.text.tag_config("l", foreground="blue")
          expState=keyVar[0]          
          if keyVar[0] == "IDLE":
              ss1="%s  boss.expState= %s; " % (timeStr,keyVar[0])
              ss2="%s  boss Idle  " % (timeStr,)
              self.logWdg.addMsg("%s " % (ss2), tags="b")
              print self.name, ss1
          elif keyVar[0] == "INTEGRATING":
              ss1="%s  boss.expState= %s,%7.2f, file=%i " % (timeStr, expState, expTime, expId)
              ss2="%s  boss exposure %6.1f, file=%i " % (timeStr, expTime, expId)              
              self.logWdg.addMsg("%s " % (ss2), tags="b")
              print self.name, ss1                   
          else:     
              ss="%s  boss.expState= %s,%7.2f, file=%i " % (timeStr, expState, expTime, expId)
            #  self.logWdg.addMsg("%s " % (ss),)
              print self.name, ss              

    def updateEncl(self,keyVar):
        if not keyVar.isGenuine: return
        timeStr = self.getTAITimeStr()
        global encl; 
        if keyVar[0] != encl:
           if keyVar[0] > 0: enclM="open"
           else : enclM="closed"        
           self.logWdg.addMsg("%s  encl25m : %s;  " % (timeStr,enclM))           
           ss="%s  encl25m : %s;  " % (timeStr,enclM)
           print self.name, ss
           encl=keyVar[0]
        else: pass

    def updateLoadCart(self,keyVar):
        if not keyVar.isGenuine: return
        global loadCart
        ct=keyVar[0]; pl=keyVar[1]; sd=keyVar[2]
        if [ct,pl,sd] != loadCart:
            timeStr = self.getTAITimeStr()
            self.logWdg.addMsg("----------------------")
            self.logWdg.addMsg("%s  loadCart: ct=%s, pl=%s,  sd=%s;  "
                     % (timeStr,str(ct),str(pl),str(sd)))
            ss="%s  loadCart: ct=%s, pl=%s,  sd=%s;  " % (timeStr,str(ct),str(pl),str(sd))
            print self.name, ss
            loadCart=[ct,pl,sd]
        else: pass    

    def updateGstate(self,keyVar):
      if not keyVar.isGenuine:return
      global gStat
      timeStr = self.getTAITimeStr()
      if keyVar[0] != gStat:
        s1=str(keyVar[0])
        if (str(keyVar[0]) == "stopping") or (str(keyVar[0]) == "failed") : 
            self.logWdg.addMsg("%s  guider = %s;  " % (timeStr, s1), severity=self.redWarn)
            ss="%s  guider = %s;  " % (timeStr, s1)
            print self.name, ss
        else:
            self.logWdg.addMsg("%s  guider = %s;  " % (timeStr, s1))
            ss="%s  guider = %s;  " % (timeStr, s1)
            print self.name, ss
        gStat=keyVar[0]

    def updateGexptime(self,keyVar):
        if not keyVar.isGenuine: return
        global gexpTime
        if keyVar[0] != gexpTime:
            timeStr = self.getTAITimeStr()       
            self.logWdg.addMsg("%s  guider.expTime = %s;  " % (timeStr, str(keyVar[0])))
            ss="%s  guider.expTime = %s;  " % (timeStr, str(keyVar[0]))
            print self.name, ss
            gexpTime=keyVar[0]

    def guideCorrFun(self,keyVar):        
      if not keyVar.isGenuine: return
      global guiderCorr
      def sw(v):
        if str(v) == "True": s="y"
        else: s="n"
        return s
      ax=keyVar[0];  foc=keyVar[1]; sc=keyVar[2]
      if [ax,foc,sc] != guiderCorr:
        timeStr = self.getTAITimeStr()
        self.logWdg.text.tag_config("g", foreground="DarkGrey")
        self.logWdg.addMsg("%s  guider.Corr:  %s %s %s  (ax foc sc);  "
              % (timeStr, sw(ax),sw(foc),sw(sc)), tags="g")
        ss="%s  guider.Corr:  %s %s %s  (ax foc sc);  " % (timeStr, sw(ax),sw(foc),sw(sc))
        print self.name, ss
        guiderCorr=[ax,foc,sc]
       
    def updateGtfStateFun(self,keyVar):    # gotoField 
        if not keyVar.isGenuine:  return
        global gtfState
        if keyVar[0] != gtfState:
          timeStr = self.getTAITimeStr()
          self.logWdg.addMsg("%s  sop.gotoField = %s;  " % (timeStr,keyVar[0]))
          ss="%s  sop.gotoField = %s;  " % (timeStr,keyVar[0])
          print self.name, ss
          gtfState=keyVar[0]
    def updateGtfStagesFun(self,keyVar):  
        if not keyVar.isGenuine:  return
        global gtfStages
        if keyVar[0] != gtfStages:
          timeStr = self.getTAITimeStr()
          self.logWdg.addMsg("%s  sop.gotoField.stages = %s;  " % (timeStr,keyVar[0]))
          ss="%s  sop.gotoField.stages = %s;  " % (timeStr,keyVar[0])
          print self.name, ss
          gtfStages=keyVar[0]

    def updateCalStateFun(self,keyVar):   # doCalibs
        if not keyVar.isGenuine: return
        global calState
        if keyVar[0] != calState:
            timeStr = self.getTAITimeStr()
            self.logWdg.addMsg("%s  sop.doCalibs = %s;  " % (timeStr,keyVar[0]))
            ss="%s  sop.doCalibs = %s;  " % (timeStr,keyVar[0])
            print self.name, ss
            calState=keyVar[0]

    def updateSciStateFun(self,keyVar):     # doScience 
        if not keyVar.isGenuine:  return
        global sciState
        if keyVar[0] != sciState:
          timeStr = self.getTAITimeStr()
          self.logWdg.addMsg("%s  sop.doScience = %s;  " % (timeStr,keyVar[0]))
          ss="%s  sop.doScience = %s;  " % (timeStr,keyVar[0])
          print self.name, ss
          sciState=keyVar[0]

    def updateFunSos1(self,keyVar):        
        if not keyVar.isGenuine: return  
      #  if keyVar[0] != sosSp1:  return
        sr=self.sr         
        self.sp1Res=self.sosModel.sp1Residuals[0:3]        
        timeStr = self.getTAITimeStr()
        ss="%s  hartSp1: r=%s, b=%s, txt=%s, sp1Temp = %s" % (timeStr,str(keyVar[0]),str(keyVar[1]),keyVar[2],self.bossModel.sp1Temp[0])        
        self.logWdg.addMsg("%s " % ss,  tags="a")
        print self.name, ss           

    def updateFunSos2(self,keyVar): 
        if not keyVar.isGenuine: return
 #       if keyVar[0] != sosSp2:    return
        sr=self.sr 
        self.sp2Res=self.sosModel.sp2Residuals[0:3]     
        timeStr = self.getTAITimeStr()
        ss="%s  hartSp2: r=%s, b=%s, txt=%s, sp2Temp = %s" % (timeStr,str(keyVar[0]),str(keyVar[1]),keyVar[2], self.bossModel.sp2Temp[0])
        self.logWdg.addMsg("%s" % ss, tags="a")
        print self.name, ss    


    def updateNeLamp(self,keyVar):
        if not keyVar.isGenuine: return
        ll=[keyVar[0],keyVar[1],keyVar[2],keyVar[3]]
        if ll !=self.neLamp:
            timeStr = self.getTAITimeStr()
            ss="%s  mcp.neLamp = %s%s%s%s"% (timeStr,str(ll[0]),str(ll[1]),str(ll[2]),str(ll[3]))
            print self.name, ss
        #    self.logWdg.addMsg("%s %s" % (self.name,ss))
            self.neLamp=ll
            
    def updateHgCdLamp(self,keyVar):
        if not keyVar.isGenuine: return
        ll=[keyVar[0],keyVar[1],keyVar[2],keyVar[3]]
        if ll != self.hgCdLamp:
            timeStr = self.getTAITimeStr()
            ss="%s  mcp.hgCdLamp = %s%s%s%s" % (timeStr,str(ll[0]),str(ll[1]),str(ll[2]),str(ll[3]))
            print self.name, ss
         #  self.logWdg.addMsg("%s %s" % (self.name, ss))
            self.hgCdLamp=ll
            
    def updateFFlamp(self,keyVar):
        if not keyVar.isGenuine: return
        ff=[keyVar[0],keyVar[1],keyVar[2],keyVar[3]]        
        if ff != self.FFlamp:
            timeStr = self.getTAITimeStr()
            ss="%s  mcp.FFlamp=%s%s%s%s " % (timeStr,str(ff[0]),str(ff[1]),str(ff[2]),str(ff[3]))
            print self.name, ss
         #   self.logWdg.addMsg("%s %s" % (self.name, ss))
            self.FFlamp=ff

    def updateFFS(self,keyVar):
        if not keyVar.isGenuine:
          return
        ssp=""
        for i in range(0,8):
           p0=str(keyVar[i])[0];  p1=str(keyVar[i])[1]
           if p0=="0" and p1=="0":  sp="?"
           elif p0=="0" and p1=="1": sp="0"
           elif p0=="1" and p1=="0": sp="1"
           else: sp="?"
           ssp=ssp+sp
        timeStr = self.getTAITimeStr()
        if ssp != self.FFs:
             ss="%s  mcp.FFs= %s " % (timeStr,ssp)
             print self.name, ss
            # self.logWdg.addMsg("%s  %s " % (timeStr, ss))
             self.FFs=ssp      
                    
    def stopCalls(self,):
        self.apoModel.encl25m.removeCallback(self.updateEncl)
        self.guiderModel.cartridgeLoaded.removeCallback(self.updateLoadCart)
        self.sopModel.gotoFieldState.removeCallback(self.updateGtfStateFun)
     #   self.sopModel.gotoFieldStages.removeCallback(self.updateGtfStagesFun)
        self.guiderModel.guideState.removeCallback(self.updateGstate)
        self.guiderModel.expTime.removeCallback(self.updateGexptime)
        self.guiderModel.guideEnable.removeCallback(self.guideCorrFun)
     #   self.sopModel.doCalibsState.removeCallback(self.updateCalStateFun)
    #    self.sopModel.doScienceState.removeCallback(self.updateSciStateFun)
        self.sosModel.sp1Residuals.removeCallback(self.updateFunSos1)
        self.sosModel.sp2Residuals.removeCallback(self.updateFunSos2)
        self.logWdg.addMsg("-----------")        
        self.logWdg.addMsg("      stopped")

    def run(self, sr):
        pass
      #  self.stopCalls()
    
    def end(self, sr):
       pass
    

