"""Sous-processus réel, nécessaire car spade.run ferme sa boucle globale."""
import asyncio,json,spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
PASSWORD="indusguard-local-dev";received=asyncio.Event();result={}
class Receiver(Agent):
    class Receive(OneShotBehaviour):
        async def run(self):
            msg=await self.receive(timeout=10)
            if msg: result.update(json.loads(msg.body));received.set()
    async def setup(self):self.add_behaviour(self.Receive(),Template(metadata={"performative":"inform","message-type":"probe"}))
class Sender(Agent):
    class Send(OneShotBehaviour):
        async def run(self):
            msg=Message(to="integration_receiver@localhost",body=json.dumps({"transport":"xmpp","value":42}));msg.sender=str(self.agent.jid);msg.set_metadata("performative","inform");msg.set_metadata("message-type","probe")
            msg.prepare(self.agent.client).send()
    async def setup(self):self.add_behaviour(self.Send())
async def main():
    receiver=Receiver("integration_receiver@localhost",PASSWORD);sender=Sender("integration_sender@localhost",PASSWORD)
    await receiver.start(auto_register=True);await sender.start(auto_register=True);await asyncio.wait_for(received.wait(),15)
    print("REAL_XMPP_OK",json.dumps(result));await sender.stop();await receiver.stop()
if __name__=="__main__":spade.run(main(),embedded_xmpp_server=True)
