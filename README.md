# Server-side
## VSCServer.py
The Server connecting all the equipmment is called *VSCServer.py* and is simply launched in the command prompt from the folder *Server*.
### Adding server commands
Server commands can be launched together with a command keyword. The keywords are linked together in a dictionary *cmd_dict* inside the server class.
The function linked should be an async function with one argument (The data sent from the extension). A command should only consist of a maximum of four letters. The system wont break if this is violated, but is better for readability and consistency.
Sending a message to the server and client is done with the string format "*command* *data*\r\n". 

### Adding an action
When creating an action a new class is created with a baseclass Action. An action can be created in a seperate file if VSCAction.py grows to large, but an action needs to be added in the Actionfactory to work.
  
#### Action functionality
The action must contain a NAME variable which is used when calling the action and handling it. The DEVICES and ACTIONS variables are lists containing the name of which acitons the current action is dependent on. For example, the take a break action is dependent on the estimate action.
These dependencies make sures no action is on when not supposed to.
The important functions in the action class are:
1. _execute(self) -_ This function gets called when its time for the action to do some work. (Overwrite)
2. _breakdown(self) -_ This function gets called when the system exits. (Overwrite)
3. self._msg_client(message) -_ This function sends a message to the client and does not get a response. (Call)
4. self._msg_client_wait(message) -_ This function sends a message to the client and waits for a response. (Call)

  Settings are a keyword together with a function. When editing an action the command EACT (Edit action) is used the command can look as following: "EACT SRVY TIME 10".
  Here EACT is the server command, SRVY is the name of the action, TIME is the setting name and 10 is the data (time in minutes in this case). 
  
  When sending a response to an action from the client the command format is as follows: "ACT *action name* *data*".
  
  ## Dashboard
  The dashboard is started with the command python app.py in the Dashboard directory.
  
