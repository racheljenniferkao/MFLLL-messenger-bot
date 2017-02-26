# MFLLL-messenger-bot

## Introduction
We made at the 2017 [Buildathon](1). This project is an exploration into combining facebook's [messenger platform](2) with the [twine method of interactive story development](3). Given that the messenger platform is a great conversational tool and twines are a limited response medium, they seemed like a great fit! We decided to test out the combination with the excellent twine [My Father's Long Long Legs](4) by [Michael Luke](5).

[1]: https://buildathon.devpost.com
[2]: https://developers.facebook.com/docs/messenger-platform
[3]: http://twinery.org
[4]: http://correlatedcontents.com/misc/Father.html
[5]: http://correlatedcontents.com

## Running the project.
Requires `python3`.
```
git clone https://github.com/racheljenniferkao/MFLLL-messenger-bot
pip3 install -r requirments.txt
```
You'll need an app token from Facbook. Edit `app.py` and insert the token where it's missing. Insert a verify token as well. Set up the bot according to Facebook's protocols. [This page](6) might help. Then:

[6]: https://blog.hartleybrody.com/fb-messenger-bot/

```
python3 app.py
```
