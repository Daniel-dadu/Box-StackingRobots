import flask
from flask.json import jsonify
import uuid
from model import Floor

games = {}

app = flask.Flask(__name__)

@app.route("/", methods=["POST"])
def create():
    global games
    id = str(uuid.uuid4())
    games[id] = Floor()
    return "ok", 201, {'Location': f"/{id}"}

@app.route("/<id>", methods=["GET"])
def queryState(id):
    global model
    model = games[id]
    model.step()

    robots = []
    boxes = []

    for agent in model.schedule.agents:
        if(str(type(agent).__name__) == "Robot"):
            robots.append({
                "x": float(agent.pos[0]), 
                "y": float(agent.pos[1]), 
            })
        else:
            boxes.append({
                "x": float(agent.pos[0]), 
                "y": float(agent.pos[1]), 
                "height": float(agent.height)
            })

    stacks = []

    for stack in model.boxStacks.keys():
        stacks.append({"x": stack[0], "y": stack[1]})

    return jsonify({"robots": robots, "boxes": boxes, "stacks": stacks})


app.run()