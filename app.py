import os
import sys
import json
import time
import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == "":
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200

def next_response(payload):
    item = states[int(payload)]
    return item

@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    mark_seen(sender_id)

                    if 'text' not in messaging_event["message"]:
                        continue
                    elif 'quick_reply' in messaging_event["message"]:
                        payload = messaging_event["message"]["quick_reply"]["payload"]
                        item = next_response(payload)
                        texts = item[0]
                        total_texts = len(texts)
                        quick_replies = item[1]
                        for i in range(total_texts):
                            if i != total_texts - 1:
                                mark_typing(sender_id)
                                send_message(sender_id, texts[i])
                                time.sleep(3)
                                unmark_typing(sender_id)
                            else:
                                mark_typing(sender_id)
                                send_message_with_clicks(sender_id, texts[i], quick_replies)
                                unmark_typing(sender_id)
                    else:
                        send_message_with_clicks(sender_id, "Welcome to \"My Father's Long Long Legs\", this is an interactive narrative fiction, click play to begin! To restart at any time, type 'restart'", [("PLAY", "0")])

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def mark_typing(recipient_id):
    log("marking typing for {recipient}".format(recipient=recipient_id))

    params = {
        "access_token": ""
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": "typing_on"
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def unmark_typing(recipient_id):
    log("unmarking typing for {recipient}".format(recipient=recipient_id))

    params = {
        "access_token": ""
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": "typing_off"
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def mark_seen(recipient_id):
    log("marking seen for {recipient}".format(recipient=recipient_id))

    params = {
        "access_token": ""
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": "mark_seen"
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": ""
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

# responses is of the form
# [ ("PLAY", "RESPONSE_0"), ("OPTION 2", "RESPONSE_1") ]
def send_message_with_clicks(recipient_id, message_text, responses):
    log("sending with response options message to {recipient}: {text}; {responses}".format(recipient=recipient_id, text=message_text, responses=responses))

    params = {
        "access_token": ""
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    quick_replies = []
    for response_option in responses:
        quick_reply = {}
        quick_reply["content_type"] = "text"
        quick_reply["title"] = response_option[0]
        quick_reply["payload"] = response_option[1]
        quick_replies.append(quick_reply)

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text,
            "quick_replies": quick_replies
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()

states = [
    (["My family lived on the southern edge of a certain Midwestern industrial city in an old house, old enough that its basement still had a dirt floor."], [("dirt floor", "1")]),
    (["I was not yet old enough to openly question a parent's behavior, but certainly old enough to recognize its oddness, when my father began digging."], [("digging", "2")]),
    (["I retain only a single clear memory of the time before the situation became alarming, and my father forsook sunlight forever."], [("single clear memory", "3")]),
    (["I am sitting at the bottom of the wooden stairs that led down to our basement. Ahead, in the dimness, stands my father, up to his waist in the hole."], [("the hole", "4")]),
    (["Still in his dark blue uniform from the factory, skin and fabric blackened by the hot breath of machinery and further smudged now by the damp earth...", "I watch Father with the satisfaction of a child who sees in her parent a well of limitless capability."], [("limitless capability", "5")]),
    (["Upstairs, my mother called out that dinner is done.", "My father takes one last shovel of earth, turns it over the side of the excavation, and - in a single incredible motion - crawls out of the hole simply by pressing the sole of his boot to the lip of the pit and moving his whole body upward, walking right past me, right up the stairs."], [("past me", "6")]),
    (["He was always a tall, angular man, as the remaining pictures of him suggest, and to this day I can clearly conjure the marvelous image of my father's long, long legs striding over me as he emerged from the hole he was to spend years digging beneath our house."], [("my father's long, long legs", "7")]),
    (["Apart from him, there were three of us: my mother, my younger brother, and myself."], [("mother", "8"), ("brother", "9"), ("myself", "10")]),
    (["There are many things about my mother I do not understand.", "She first found my father attractive, she admitted to me many years later, because of how unusual he was."], [("unusual", "11")]),
    (["My brother was young enough when my father began digging that it seemed to him an indifferent fact of life."], [("fact of life", "38")]),
    (["A year or so before we left my father was the last time I ventured down into the basement."], [("ventured down", "24")]),
    (["He had come to the Midwestern industrial town and secured a job at the same factory where my mother was working.", "Though a practical man, he read constantly and voraciously in subjects ranging from engine repair to philosophy — a habit instilled in him, he had claimed, by his own parents."], [("his own parents", "12")]),
    (["This was all my father ever said of his family beyond us; any further inquiry into the subject caused him to leave the room, or bring up some other pressing issue.", "Mother once theorized that Father had run away from home."], [("run away from home", "13")]),
    (["Whatever his reasons for leaving his family behind, my father did not wait too long before beginning a new one.", "I was born only a few months after my parents were married."], [("were married", "14")]),
    (["Within a few years Father made enough money that my mother could stay home and watch over me and, not too long after, my brother.", "Then one night, when my brother was perhaps only a year old, Father came home, pulled a brand-new shovel from the back of his pickup truck, and descended into the basement, where he began to dig."], [("to dig", "15")]),
    (["At first he told Mother that he was preparing to put down a cement floor, suggesting a prelude to a full or partial renovation of the house.", "As a child, the movements of adults were still largely mysterious to me, and I do not know the specific circumstances under which Mother's realized this motive was untrue."], [("untrue", "16")]),
    (["Nor do I know exactly what transpired when Father told Mother that they must go to the basement to discuss the matter closer to its source, for after the door shut behind them, my brother and I were left alone in the house."], [("alone in the house", "17")]),
    (["My brother cried most of the night while I lay in my own bed, pillows pressed to my ears.", "The next day my mother reappeared, quietly prepared our meals, and then locked herself in her bedroom shortly before Father returned home and commenced digging once again."], [("once again", "18")]),
    (["My father, for his part, stopped sleeping in the bedroom with her, instead taking to the basement, a decision which coincided with the first signs of his terrible metamorphosis."], [("metamorphosis", "19")]),
    (["The changes were slow, but noticeable. Father began to grow paler, and by the time the factory closed and he could spend the whole day in the basement, he was as white as chalk.", "Perhaps it was this general evidence of wear, the change in skin tone and his subsequent emaciation, that made him look taller, as if his height increased in proportion to the depth of his project in the basement.", "Meanwhile, my mother put my brother into pre-school and sent me to a latch-key program while she worked to support us. In what seemed a deliberate contrast to my father, she grew somehow darker, and smaller."], [("darker, and smaller", "20")]),
    (["My father dug uninterrupted in the basement for at least a decade, and once I started high school he did not even leave the basement to join us for dinner.", "Then my mother left him."], [("left him", "21")]),
    (["Father was sufficiently enveloped in his life's task that there was no need to replay the arguments from my childhood — whatever desire he once had to keep us home with him had apparently fallen away, lost in the depths of that pit."], [("keep us home", "22")]),
    (["On her own, Mother seemed to physically decompress, to become less bowed. She spoke more, laughed more. She had friends and lovers.", "We did not see my father at all after we left."], [("did not see my father", "23")]),
    (["On the day we left for good he did not even come out of the basement, though by that point it was questionable how easily he could get through the doorway, so tall he had grown.", "It was not until many years later that my brother suggested we pay a return visit to our father's house."], [("our father's house", "54")]),
    (["My brother was out with friends, having reached the age when he finally realized the awkwardness that resulted from bringing visitors to our home, and Mother had locked the door to her room and apparently gone to bed.", "Father was, of course, laboring in the basement, and I was doing homework in the living room while watching television.", "There came a knock at the door."], [("knock at the door", "25")]),
    (["The man on the porch was squat, but dressed neatly in a suit, coat, and hat. A pair of very small spectacles was perched on the end of his nose, looking miniscule in comparison to his large, round face.", "\"Hello, young lady,\" he said to me in a labored voice. \"Is your father home?\""], [("father home?", "26")]),
    (["\"Who are you?\" I asked.", "The man tipped his old-fashioned hat back on his head, smiling with rubbery lips. \"You would have no reason to know me, of course,\" he said, \"but I'm your uncle.\""], [("your uncle", "27")]),
    (["I left the man on the porch, the door locked, while I went to seek my mother's help. (Thus I discovered she was unresponsive, as she often was in those days.)", "This left me with only the option to summon my father from the basement."], [("summon my father", "28")]),
    (["He did not respond when I opened the door and yelled down, though I thought I could hear, faintly, the sound of his digging.", "I looked back to the front door, where I could see through pebbled glass the rotund figure of the man who claimed to be my uncle, and descended the wooden stairs into the basement."], [("descended the wooden stairs", "29")]),
    (["The only light, as always, came from a single bulb hanging from the ceiling.", "My father had learned to operate in these conditions, but for me, the lack of illumination cast the labyrinth below into a mess of confusing and seemingly contradictory paths of damp black earth and only slightly blacker shadow."], [("slightly blacker shadow", "30")]),
    (["Father had first attempted to dig straight down, but as the years went on he elaborated his original plans, angling outward from the center of the basement at a depth of perhaps fifteen feet.", "From there he had begun to hollow out the entirety of the basement with one long, looping path, threaded and bent around itself like some monstrous length of viscera, all the while continuing his march downward."], [("his march downward", "31")]),
    (["I stood on the bottom-most stair that, as I thought of it, still properly belonged to our house.", "By my feet was a stack of unfamiliar books. They were old, with blank but warped brown covers. Next to them was what appeared to be an antique child's rattle, caked with dirt, and several rocks chipped into various unnatural but vaguely instrumental shapes.", "I turned to the void and called for my father."], [("called for my father", "32")]),
    (["No response came, but I grew more certain than I could hear, however distantly, the sound of Father's shovel.", "I called for him again, this time giving also my purpose for interrupting his work. \"There's a man at the door!\" I said. \"He says he's my uncle.\"", "I stood and waited, and as I did so, the sound of digging stopped."], [("stopped", "33")]),
    (["My father emerged a minute or so later, unfolding himself from the narrow bends of his maze, his pale skin covered only by the rags of his clothing and everywhere dusted gray with soil — including, I noted, the corners of his mouth, which seemed stained particularly thoroughly, and much more darkly.", "\"Your uncle,\" Father rumbled, not quite asking a question. He then added: \"My brother.\"", "I nodded.", "\"Show him in,\" he ordered."], [("Show him in", "34")]),
    (["The squat stranger — my uncle, who I remember smelled of sour milk — seemed elated at his prospects.", "I led him down the basement stairs, his agitation growing exponentially until he saw my father standing at his full height (it must have been at least eight or nine feet then, I think) at the entrance of his renovations.", "I knew to take my leave, and as I ascended the stairs I heard the visitor remark that my father seemed to have \"done very well\" for himself, \"all things considered.\""], [("very well", "35")]),
    (["I never again saw the man who claimed to be my uncle, either that day or any day after.", "Perhaps not coincidentally, this is also my last clear memory of my father, and the one that returned to me many years later when my brother suggested we return to our father's house."], [("our father's house", "54")]),
    (), #(["Needless to say, my brother and I had different experiences of our early home life."], [("brother", "9"), ("I", "37")]),
    (), # I
    (["It seemed obvious to me that something was wrong with our home. Its wrongness was screamed, I thought, by the chilly terseness with which our mother moved through it, returning home from work in the late afternoon, serving meals, and retiring to her bedroom.", "The wrongness was screamed, of course, by my father, who after losing his job at the factory spent nearly all day in the basement, emerging at irregular intervals to eat and use the toilet. (This is to say nothing of the physical changes he underwent as time went on.)"], [("time went on", "39")]),
    (["The wrongness was screamed by my own actions, the heavy worry I felt that at any moment the fragile equilibrium of our home would be upset and my brother's friends would witness the terrifying truth of our family's situation — a situation I myself could not begin to articulate, but which I felt ashamedly that an outsider would.", "Of course my brother, young as he was, saw nothing wrong with inviting his friends to our home, and even taking them down to the basement to see what he called — after our father's example, I believe — \"the renovations.\""], [("the renovations", "40")]),
    (["The friends never asked to return to the basement after my brother took them down there. Some of them quietly deigned to never return to our house at all — much to my relief, though my brother was often disappointed.", "I recall only one instance, when my brother was perhaps seven, when one of his playmates made a scene."], [("a scene", "41")]),
    (["I believe my brother's friend came from a religious family, which may have been part of the problem, but that may also be something I recognize only due to my own biases.", "At any rate, though his cosmology was different from my own, he at least shared some of my anxieties when he attempted to explain to my brother that our father's project in the basement was deeply unnatural."], [("deeply unnatural", "42")]),
    (["I emerged from the living room because, down the hall, I could hear crying. I knew that my brother had a friend over, and so was prepared for the worst.", "The two boys stood outside the door to the basement, which still stood open. My brother looked up as I approached, at a loss as to how to comfort his weeping companion."], [("weeping companion", "43")]),
    (["\"You're going to Hell,\" our visitor informed me, after I managed to get him to look at me.", "\"That's where he's digging to down there,\" the child said, looking from me to my brother. \"He's digging to Hell, and you're all going with him.\""], [("going with him", "44")]),
    (["My brother did not invite as many classmates over after that day, and I don't believe he ever invited any of them down to see \"the renovations\" ever again."], [("ever again", "45")]),
    (["\"Are we really going to Hell?\" he asked me one night, lying beside me in bed after a nightmare sent him to my room.", "I told him I did not know.", "\"But is that where Dad is digging to?\" he asked.", "I told him there was no such place.", "\"Then why is Dad digging?\""], [("why", "46")]),
    (["In the early days, when I sat on the stairs and watched him work, my father had given me dozens of flippant reasons for his project: seeking dinosaur bones.", "All of these excuses had lost currency by this point, of course, and when asked what he was doing — as, my brother told me, his religious visitor had inquired — my father had other things to say."], [("other things to say", "48")]), # [("seeking dinosaur bones", "47"), ("other things to say", "48")]),
    (),# seeking dinosaur bones
    (["\"This is not the real world,\" my father would say, or something along these lines."], [("something along these lines", "49")]),
    (["\"What we think is the real world is just a layer of dirt caked around the true core of the universe.\""], [("the true core of the universe", "50")]),
    (["\"And what is dirt? Inert matter! Dead weight! The remains of those who came and went before us, content only to further press down upon Creation with their waste.\""], [("their waste", "51")]),
    (["\"There was a time when human beings were giants walking upon a small Earth, but now the Earth has grown fat and hateful with our soil, while we have grown small.\""], [("we have grown small", "52")]),
    (["\"Starting here, I am scraping away this sediment, our coagulated filth, and returning us to our original glory.\""], [("our original glory", "53")]),
    (["I assemble this manifesto from memory, from various iterations and variations Father offered us over the years, and certainly it was the sort of heresy that had offended my brother's erstwhile friend.", "Still, they were not satisfactory answers to us then, and would not be satisfactory for my brother as he huddled, fearing Hell, in my bed.", "But frankly, I had no other answer for him, and let the matter lapse into silence.", "Which is perhaps why, all those years later, he urged me to come with him back to our father's house."], [("our father's house", "54")]),
    (["It seemed my brother wanted to put his mind at ease by checking up on our father, who had been left alone now for slightly longer than we had lived with him.", "On the one hand I appreciated my brother's sentiment, even if I felt it was misplaced. On the other hand, I knew I could not stop him. His feelings toward Father had always been more lenient.", "The only question was: would I go along with him, or let him make the visit on his own?"], [("go along with him", "55"), ("on his own", "56")]),
    (["We decided upon a day to visit our childhood home, where we assumed our father still lived, and decided to meet there one afternoon the following week.", "But there must have somewhere been a miscommunication."], [("miscommunication", "57")]),
    (["I was so sorely mistaken."], [("mistaken", "58")]),
    (["I was late.", "I must have been late — the alternative is that, for his own purposes, my brother arrived early, to see our father before I did.", "And I do not wish to contemplate why that would be."], [("why that would be", "59")]),
    (["After learning I wouldn't accompany him, and despite my urging him to give up on the plan, my brother went anyway, alone.", "After several days of him not responding to my calls, I had no choice but to follow."], [("follow", "59")]),
    (["The town was considerably less industrial than it had been, though the taste of industry still laced our water and air. The old neighborhood, not the most affluent even in former times, had fallen into further disrepair." "The houses up and down the block stood weathered and, it seemed, empty. The sidewalks buckled around thick protrusions of sickly weeds, which reached out into the pot-holed street, protruding fingers of the overgrown lawns.", "The only sign of habitation was a single car, my brother's car, parked outside our old home."], [("my brother's car", "60")]),
    (["The doors were locked, the windows rolled up. A hand pressed to the hood told me it was not warm, but apart from that I had no way of guessing how long the vehicle had been there unattended.", "Ahead, the house waited."], [("the house", "61")]),
    (["It seemed not much different from the rest of the buildings, scraped down to gray bones by the elements.", "The windows were gone, without even slivers of glass remaining, and the porch had bowed and now held a stagnant pool of rainwater.", "The front door stood open at an angle, its lowermost hinge having rusted and snapped in two."], [("front door stood open", "62")]),
    (["Stepping carefully on the rotten porch, I slipped inside and found myself in the old living room.", "The floor was littered with trash and chunks of plaster dropped from the ceiling. The television was gone, though a lighter patch in the shredded wallpaper marked its former location. The couch had collapsed and now seemed covered with mounds of some sort of gray mold or fungus.", "Ahead was the central hallway of the house, and I could see that the door to the basement had been wholly removed."], [("door to the basement", "63")]),
    (["I called out my brother's name and then stood for a moment, looking down into unremitting darkness.", "Of course the power was out. It was probably disconnected long ago.", "But a flashlight lay on the floor just outside the basement entrance."], [("flashlight", "64")]),
    (["My brother's?", "The flashlight seemed quite new. I flicked it on and pointed it down into the basement, but it penetrated far enough only to reveal the foot of the stairs.", "I called my brother's name again, and waited.", "There was still no response."], [("no response", "65")]),
    (["Assuming the basement was anything like as I had last seen it, my brother could have easily gotten hurt if he went down without his flashlight.", "He might have been lying down there just beyond the stairs, unconscious.", "I had to make sure."], [("I had to make sure", "66")]),
    (["Flashlight ready, I went into the basement."], [("basement", "67")]),
    (["The stairs creaked beneath my feet.", "I reached the bottom,", "and when my flashlight returned only a slope heading deeper beneath the house,", "I knew my father had done quite a bit of work in the decade since we left."], [("quite a bit of work", "68")]),
    (["I went down.", "I called for my brother.", "I walked to the left.", "I walked to the right."], [("down", "69"), ("called", "70"), ("left", "71"), ("right", "72")]),
    (["I called for my brother again.", "I turned right.", "The musty smell of old earth filled my nostrils."], [("called", "73"), ("right", "74"), ("musty smell of old earth", "75")]),
    (["I continued onward."], [("onward", "85")]), # called
    (["I continued onward."], [("onward", "85")]), # left
    (["I continued onward."], [("onward", "85")]), # right
    (["Only my own breathing echoed back through those chambers of barren earth.", "I walked further into the darkness."], [("chambers of barren earth", "76"), ("into the darkness", "77")]),
    (["I continued onward."], [("onward", "85")]), # right
    (["I continued onward."], [("onward", "85")]), # musty smell of old earth
    (["Around me there was nothing but darkness."], [("nothing but darkness", "78")]),
    (["I continued onward."], [("onward", "85")]), # into the darkness
    (["I walked further onward.", "I called for my brother again, and received no answer.", "I followed the sound of digging.", "The path branched, left and right."], [("further onward", "79"), ("called", "80"), ("no answer", "81"), ("digging", "82"), ("left", "83"), ("right", "84")]),
    (["I continued onward."], [("onward", "85")]), # further onward
    (["I continued onward."], [("onward", "85")]), # called
    (["I continued onward."], [("onward", "85")]), # no answer
    (["I continued onward."], [("onward", "85")]), # digging
    (["I continued onward."], [("onward", "85")]), # left
    (["I continued onward."], [("onward", "85")]), # right
    (["I did not find my brother."], [("find my brother", "86")]),
    (["I do not know what to tell our mother. I do not know where to go from here, what to do.", "It is true I gave up my search, but once I saw what lived there — had been living there for all these years, or more precisely what had grown there — I ran from the basement."], [("ran", "87")]),
    (["Somehow — by my own luck or by some other's design — I made it out of that darkness, though my brother has not.", "There is a chance, I think, that he may still be alive."], [("still be alive", "88")]),
    (["My guilt is heavy, do not doubt that.", "But it is outweighted by the fear I experienced when I came face to face with that terrible result of Father's attempted renovations of a rotted world."], [("attempted renovations of a rotted world", "89")]),
    (["I once told my brother there is no such place as Hell."], [("Hell", "90")]),
    (["I still believe that to be true.", "But wherever my little brother is now..."], [("But wherever my little brother is now...", "91")]),
    (["I wonder if he's grown as tall as our father?"], [("play again", "0")])
]


if __name__ == '__main__':
    app.run(debug=True)
