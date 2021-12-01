using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
// Clase que define un robot
class Robot{
    public float x;
    public float y;
    public bool hasBox;
}

[System.Serializable]
// Clase que define una caja
class Box{
    public float x;
    public float y;
    public float height;
}

[System.Serializable]
// Clase que define las pilas o estantes
class Stack{
    public float x;
    public float y;
}

// Clase que cuenta con todo el contenido
class Agents{
    public List<Robot> robots;
    public List<Box> boxes;
    public List<Stack> stacks;
    public bool isRunning;
}

public class MovementModel : MonoBehaviour{

    float timer = 0.0f;
    bool firstIterationFlag = true;
    bool modelIsRunning = true;

    GameObject[] robotsGame;
    GameObject[] lightsGame;
    GameObject[] boxesGame;
    GameObject[] stacksGame;

    public GameObject robotPrefab;
    public GameObject lightPrefab;
    public GameObject boxPrefab;
    public GameObject stackPrefab;

    string simulationURL = null;
    int numRobots = 5; // Hardcoded porque no lo puedo mandar desde el ConnectToMesa
    int numBoxes = 15; // Hardcoded porque no lo puedo mandar desde el ConnectToMesa
    int numStacks;

    // Start is called before the first frame update
    void Start(){
        StartCoroutine(ConnectToMesa());

        numStacks = (int)(numBoxes / numRobots) + (numBoxes%numRobots == 0 ? 0 : 1);

        robotsGame = new GameObject[numRobots];
        lightsGame = new GameObject[numRobots];
        boxesGame = new GameObject[numBoxes];
        stacksGame = new GameObject[numStacks];

        // Created this far position so that the objects cannot be seen when created 
        Vector3 farPos = new Vector3(20,0,0);

        // Creamos los robots y sus luces puntuales
        for (int i = 0; i < numRobots; i++){
            robotsGame[i] = Instantiate(robotPrefab, farPos, Quaternion.identity);
            robotsGame[i].transform.localScale = new Vector3(0.01f, 0.01f, 0.01f);

            lightsGame[i] = Instantiate(lightPrefab, farPos, Quaternion.identity);
            lightsGame[i].transform.localScale = new Vector3(0.01f, 0.01f, 0.01f);
        }

        // Creamos las cajas
        for (int i = 0; i < numBoxes; i++){
            boxesGame[i] = Instantiate(boxPrefab, farPos, Quaternion.identity);
            boxesGame[i].transform.localScale = new Vector3(0.01f, 0.01f, 0.01f);
        }
        
        // Creamos los estantes
        for (int i = 0; i < numStacks; i++){
            stacksGame[i] = Instantiate(stackPrefab, farPos, Quaternion.identity);
            stacksGame[i].transform.localScale = new Vector3(0.001f, 0.001f, 0.001f);
        }

    }

    // Función que permite hacer la conexión con la API y obtener el ID del juego a través del método post
    IEnumerator ConnectToMesa(){
        WWWForm form = new WWWForm();

        using(UnityWebRequest www = UnityWebRequest.Post("http://localhost:5000/", form)){
            yield return www.SendWebRequest();

            if (www.result != UnityWebRequest.Result.Success)
                Debug.Log(www.error);
            else{
                simulationURL = www.GetResponseHeader("Location");

                Debug.Log("Connected to simulation through Web API");
            }
        }
    }

    IEnumerator UpdatePositions(){
        using (UnityWebRequest www = UnityWebRequest.Get(simulationURL)){
            if (simulationURL != null){
                // Request and wait for the desired page.
                yield return www.SendWebRequest();

                Debug.Log(">>> JotaSON: " + www.downloadHandler.text + "");

                // Parseamos el contenido del JSON a un objeto de la clase Agentes
                Agents myAgents = JsonUtility.FromJson<Agents>(www.downloadHandler.text);

                modelIsRunning = myAgents.isRunning;

                // Iteramos por cada robot, caja y estante qe tenemos y los acomodamos de acuerdo al JSON

                for (int i = 0; i < numRobots; i++){
                    robotsGame[i].transform.position = new Vector3(myAgents.robots[i].x*0.35f, 0, myAgents.robots[i].y*0.35f);
                    robotsGame[i].transform.localScale = new Vector3(1f, 1f, 1f);

                    // En la primera iteración colocamos al robot en su rotación correcta
                    if (firstIterationFlag)
                        robotsGame[i].transform.Rotate(0f, 180f, 0f);
                    
                    if(myAgents.robots[i].hasBox){
                        // Si el robot tiene una caja, se enciende su luz
                        lightsGame[i].transform.position = new Vector3(myAgents.robots[i].x*0.35f, 0.5f, myAgents.robots[i].y*0.35f);
                        lightsGame[i].transform.localScale = new Vector3(1f, 1f, 1f);
                    } else {
                        // De lo contrario, su luz desaparece (se va lejos)
                        lightsGame[i].transform.position = new Vector3(20,0,0);
                        lightsGame[i].transform.localScale = new Vector3(1f, 1f, 1f);
                    }
                }
                
                for (int i = 0; i < numBoxes; i++){
                    boxesGame[i].transform.position = new Vector3(myAgents.boxes[i].x * 0.35f, myAgents.boxes[i].height*0.17f, myAgents.boxes[i].y * 0.35f);

                    boxesGame[i].transform.localScale = new Vector3(15f, 15f, 15f);

                    // En la primera iteración colocamos a las cajas en su rotación correcta
                    if (firstIterationFlag)
                        boxesGame[i].transform.Rotate(-90f, 0f, 0f);
                    
                }

                for (int i = 0; i < myAgents.stacks.Count; i++){
                    stacksGame[i].transform.position = new Vector3(myAgents.stacks[i].x*0.35f + 0.17f, 0, myAgents.stacks[i].y*0.35f + 0.12f);

                    stacksGame[i].transform.localScale = new Vector3(0.35f, 0.7f, 0.24f);
                }
                
                firstIterationFlag = false;
            }
        }
    }

    // Update is called once per frame
    void Update(){
        // Ponemos un tiempo de espera de .2 segundos para hacer que la simulación no vaya tan rápido
        float waitTime = 0.2f;

        timer += Time.deltaTime;
        if (timer > waitTime && modelIsRunning){
            StartCoroutine(UpdatePositions());
            timer = timer - waitTime;
        }
    }
}
