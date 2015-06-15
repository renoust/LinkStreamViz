from tulip import *
import tulipplugins
import json
import os
import sys
import random
import math

class idGenerator:
    """generates id"""

    def __init__(self):
		self.lookUp = dict()  # dict[Node] = id
		self.idCount = 0
		self.reverse = dict()  # dict[id] = node

    def impose(self, node, id_):
		self.lookUp[node] = id_
		self.reverse[id_] = node

    def contains(self, element):
		return element in self.lookUp

    def get(self, element):

		if element not in self.lookUp:
		    while self.idCount in self.reverse and self.reverse[self.idCount] != element:
				self.idCount += 1
		    self.lookUp[element] = self.idCount
		    self.reverse[self.idCount] = element
		return self.lookUp[element]

    def size(self):
		return len(self.lookUp)


class Link:

    def __init__(self, t, u, v, color="black", direction=0, duration=0, duration_color="black"):
    	self.t = float(t)
    	self.u = int(min(u, v))
    	self.v = int(max(u, v))
    	self.color = color
    	self.direction = direction
    	self.duration = duration
    	self.duration_color = duration_color

    @staticmethod
    def from_dict(link):
		obj = Link(link["time"],
				   link["from"],
				   link["to"])
		obj.color = link.get("color", "black")
		obj.direction = link.get("direction", 0)
		obj.duration = float(link.get("duration", 0))
		obj.duration_color = link.get("duration_color", "black")
		return obj


class LinkStream:
	def __init__(self, inputFile, orderFile="", graph=None):
		self.links = []
		self.max_time = 0
		self.nodeID = idGenerator()
		self.max_label_len = 0

		self.ppux = 10  # pixel per unit time

		if "json" in inputFile:
		    with open(inputFile, 'r') as inFile:
				json_struct = json.loads(inFile.read())
				for link_json in json_struct:
				    link = Link.from_dict(link_json)
				    self.addNode(link.u)
				    self.addNode(link.v)
				    if (link.t + link.duration) > self.max_time:
						self.max_time = link.t + link.duration
				    self.links.append(link)
		else:
		    with open(inputFile, 'r') as inFile:
				for line in inFile:
				    contents = line.split(" ")
				    t = float(contents[0])
				    u = int(contents[1])
				    v = int(contents[2])
				    d = 0
				    if len(contents) > 3:
						d = float(contents[3])
				    self.addNode(u)
				    self.addNode(v)
				    if t > self.max_time:
						self.max_time = t
				    self.links.append(Link(t, u, v, duration=d))
		if orderFile != "":
		    tmp_nodes = set()
		    with open(orderFile, 'r') as order:
				for i, n in enumerate(order):
				    node = int(n)
				    tmp_nodes.add(node)
				    if self.nodeID.contains(node):
						self.nodeID.impose(node, i)
						self.nodes.append(node)
				    else:
						print('The node', node, "is not present in the stream")
						exit()
		    for node in self.nodeID.lookUp:
				if node not in tmp_nodes:
				    print('The node', node, "is not present in", orderFile)
				    exit()
	
	
	def addNode(self, node):
		self.nodeID.get(node)
		if self.max_label_len < len(str(node)):
		    self.max_label_len = len(str(node))

	def evaluateOrder(self, order):
		distance = 0
		for link in self.links:
		    distance += abs(order[link.u]-order[link.v])
		return distance

	def findOrder(self):
		cur_solution = self.nodeID.lookUp
		cur_reverse = self.nodeID.reverse
		dist = self.evaluateOrder(cur_solution)
		#sys.stderr.write("Order improved from "+str(dist))
		
		for i in range(0, 10000):
		    i = random.randint(0, len(cur_solution) - 1)
		    j = random.randint(0, len(cur_solution) - 1)
		    cur_reverse[j], cur_reverse[i] = cur_reverse[i], cur_reverse[j]
		    cur_solution[cur_reverse[j]] = j
		    cur_solution[cur_reverse[i]] = i
		    tmp = self.evaluateOrder(cur_solution)
		    if tmp >= dist:
				# re swap to go back.
				cur_reverse[j], cur_reverse[i] = cur_reverse[i], cur_reverse[j]
				cur_solution[cur_reverse[j]] = j
				cur_solution[cur_reverse[i]] = i
		    else:
				dist = tmp
		self.nodeID.lookUp = cur_solution
		
		#new_order = "new_order.txt"
		#with open(new_order, "w") as out:
		#    for node in self.nodeID.reverse:
		#		out.write(str(self.nodeID.reverse[node]) + "\n")

		#sys.stderr.write(" to "+str(dist)+". Order saved in:"+new_order+"\n")

class LoadLinkflow(tlp.ImportModule):
	def __init__(self, context):
		tlp.ImportModule.__init__(self, context)
		self.addStringParameter("Path - linkflow",\
										 "Path to the linkflow file .json or .txt",\
										 "/work/localdata/Thiers-highschool-linkflow/LinkStreamViz/tests/test2.json",\
										 True)
		self.addStringParameter("Path - ordering",\
										 "Path to the ordering file .txt",\
										 "",\
										 True)

		self.addFloatParameter("Width per unit of time", "width of a node in the flow", "10", True)
		self.addFloatParameter("Edge bent", "width of something in the flow", "10", True)
		self.addFloatParameter("Height per layer", "height of a layer in the flow", "10", True)
		self.addBooleanParameter("Draw link flow", "draws the link flow", "True", True)
		self.addBooleanParameter("Draw multiplex projection", "draws the multiplex projection", "True", True)
		self.addBooleanParameter("Draw flat projection", "draws the flat projection", "True", True)
		self.addBooleanParameter("Force layout", "draws the projections with FM^3", "True", True)
		

	def importGraph(self):
		fPath = self.dataSet["Path - linkflow"]
		order = self.dataSet["Path - ordering"]
		if order == None:
			order = ""

		links = LinkStream(fPath, order)
		self.draw_tulip(links)

		return True
		
	def draw_tulip(self, _links):
		
		widthMargin = self.dataSet["Edge bent"]
		heightMargin = self.dataSet["Height per layer"]
		pixelPerUnitOfTime = self.dataSet["Width per unit of time"]
		linkFlow = self.dataSet["Draw link flow"]
		multiProj = self.dataSet["Draw multiplex projection"]
		simpleProj = self.dataSet["Draw flat projection"]
		
		_links.findOrder()
		
		################
		# Draw background lines
		vL = self.graph.getLayoutProperty("viewLayout")
		vC = self.graph.getColorProperty("viewColor")
		vS = self.graph.getIntegerProperty("viewShape")
		vLabel = self.graph.getStringProperty("viewLabel")
		origin = self.graph.getStringProperty("__original_node__")
		timeStamp = self.graph.getDoubleProperty("__timeStamp__")
		duration = self.graph.getDoubleProperty("__duration__")
		direction = self.graph.getDoubleProperty("__direction__")
		tlp_bezier_curve_shape = 4
		axisToLabel = {}
		n2axis = {}
		lg = None
		sg = None
		mg = None
		
		
		nodeToTLP = {}

		for node in _links.nodeID.lookUp:			
		    horizonta_axe = heightMargin * _links.nodeID.get(node)
		    axisToLabel[horizonta_axe] = str(node)
		    if multiProj or simpleProj:
		    	n = self.graph.addNode()
		    	origin[n] = str(node)
		    	nodeToTLP[horizonta_axe] = n

		if linkFlow:
			lg = self.graph.addSubGraph()
			lg.setName("Link flow")
			
		if multiProj:
			mg = self.graph.inducedSubGraph(nodeToTLP.values())
			mg.setName("Multiplex graph")

		if simpleProj:
			sg = self.graph.inducedSubGraph(nodeToTLP.values())
			sg.setName("Simple graph")
			timeStamps = self.graph.getDoubleVectorProperty("__timeStampList__")
			durations = self.graph.getDoubleVectorProperty("__durationList__")
			directions = self.graph.getDoubleVectorProperty("__directionList__")


		for link in _links.links:
		    ts = link.t
		    node_1 = min(_links.nodeID.get(link.u), _links.nodeID.get(link.v))
		    node_2 = max(_links.nodeID.get(link.u), _links.nodeID.get(link.v))
		    offset = ts * pixelPerUnitOfTime
		    
		    y_node1 = heightMargin * node_1
		    y_node2 = heightMargin * node_2
		    
		    color = [int(c.strip()) for c in link.color.replace('rgb(','').replace(')','').split(',')]
		    color = tlp.Color(color[0], color[1], color[2])
		    
		    
		    if linkFlow:
			    n1 = lg.addNode()
			    vL[n1] = tlp.Coord(offset, y_node1)
			    vLabel[n1] = axisToLabel[y_node1]
			    origin[n1] = axisToLabel[y_node1]
			    vC[n1] = color
	
			    n2 = lg.addNode()
			    vL[n2] = tlp.Coord(offset, y_node2)
			    origin[n2] = axisToLabel[y_node2]
			    vLabel[n2] = axisToLabel[y_node2]
			    vC[n2] = tlp.Color(color)
				 
			    x = 0.2 * ((widthMargin * node_2 - widthMargin * node_1) / math.tan(math.pi / 3)) + offset
			    y = (y_node1 + y_node2) / 2
			    
			    e = lg.addEdge(n1, n2)
			    timeStamp[e] = ts
			    direction[e] = link.direction
			    duration[e] = link.duration
			    vL[e] = [tlp.Coord(x, y)]
			    vS[e] = tlp_bezier_curve_shape
			    vC[e] = tlp.Color(color)
			    
		    if multiProj or simpleProj:
		    	n1 = nodeToTLP[y_node1]
		    	n2 = nodeToTLP[y_node2]
		    	if simpleProj:
		    		e = sg.existEdge(n1, n2, False)
		    		if not e.isValid():
		    			e = sg.addEdge(n1, n2)
		    		tSList = timeStamps[e]
		    		tSList.append(ts)
		    		timeStamps[e] = tSList
		    		durList = durations[e]
		    		durList.append(link.duration)
		    		durations[e] = durList
		    		dirList = directions[e]
		    		dirList.append(link.direction)
		    		directions[e] = dirList
		    			
		    	if multiProj:
		    		e = mg.addEdge(n1, n2)
		    		timeStamp[e] = ts
		    		direction[e] = link.direction
		    		duration[e] = link.duration
		    		vC[e] = tlp.Color(color)

		if self.dataSet["Force layout"]:
			if multiProj:
				vL = mg.getLayoutProperty("viewLayout")
				mg.applyLayoutAlgorithm("FM^3 (OGDF)", vL)
			 
			if simpleProj:
				vL = sg.getLayoutProperty("viewLayout")
				sg.applyLayoutAlgorithm("FM^3 (OGDF)", vL)
	
# The line below does the magic to register the plugin to the plugin database
# and updates the GUI to make it accessible through the menus.
tulipplugins.registerPluginOfGroup("LoadLinkflow", "Load a linkflow", "Benjamin Renoust & Jordan Viard", "15/06/2015", "Loads a linkflow", "1.0", "Linkflow")
