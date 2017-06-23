/*
 *  DataFlow v1.0 
 *  Copyright © 2012-2016 Tencent. All Rights Reserved.
 *  authors : v_fenggye 
 */
 
'use strict';
(function($){
	function DataFlow(config){
		this.config = config;
		this.dataFlowDom = $('.dataflow');
		this.templateDom = this.dataFlowDom.find('#template');					//模板 dom
		this.containerDom = this.dataFlowDom.find('#dataflow-container');		// 画布 dom
		this.nodesVue = {};	// 节点的vue集
		this.edgesVue = {};	// 线条的vue集
		this.svgDom = {};		// svg dom
		this.containerInfo = {x:0,y:0};
		this.init();
	}
	DataFlow.prototype = {
		constructor : DataFlow,
		/**
		 * [init 初始化方法]
		 * @return {[type]} [description]
		 */
		init:function(){
			var topThis = this;

			//	如果有数据源则回填数据
			if(topThis.config && topThis.config.data){
				topThis.renderData(topThis.config.data,topThis.containerDom);
			}
			this.initCreateFlowEvent();
			this.initNodeDragEvent();
			this.initConnectionEvent();
			this.getframeInfo();
			this.drag();
		},
		/**
		 * [drag 鼠标画布拖拽方法]
		 */
		drag:function(){
			var topThis = this;
			var isDrag = false;
			var curDom = this.containerDom;
			var mouseXY = [];

			if(this.config.drag){
				var parents = curDom.parent();
				var parentSize = {
					width : parents.width(),
					height : parents.height()
				};

				var curDomSize = {
					x: curDom.position().left,
					y: curDom.position().top,
					width : curDom.width(),
					height : curDom.height()
				};


				topThis.dataFlowDom.on('mousedown','#dataflow-container',function(e){
					if(1 === e.which){
						var $dom = $(e.target);

						if($dom.hasClass('dataflow-container')){
							isDrag = true;
							mouseXY['x'] = e.pageX;
							mouseXY['y'] = e.pageY;
							mouseXY['top'] = curDom.position().top;
							mouseXY['left'] = curDom.position().left;
						}
					}else{
						isDrag = false;
					}
				}).
				on('mouseup',function(e){
					isDrag = false;
				}).
				on('mouseout',function(e){
					isDrag = false;
				}).
				on('mousemove','.dataflow-container',function(e){
					if(isDrag && topThis.config.drag){
						var move = [],moveTo = [],div = [];
						var $this = $(this);

						move['x'] = e.pageX;
						move['y'] = e.pageY;

						moveTo['t'] = move['y'] - mouseXY['y'] - curDomSize.y;
						moveTo['l'] = move['x'] - mouseXY['x'] - curDomSize.x;

						var top = moveTo['t'] + mouseXY['top'];
						var left = moveTo['l'] + mouseXY['left'];

						if(top <= 0 && (parentSize.height - curDomSize.height) <= top){
							curDom.css({'top':top})
						}

						if(left <= 0 && (parentSize.width - curDomSize.width) <= left){
							curDom.css({'left':left})
						}
					}
				});
			}
		},
		/**
		 * [getframeInfo 重新获取容器相关信息]
		 */
		getframeInfo:function(){
			this.containerInfo = {
				x : this.containerDom.position().left,
				y : this.containerDom.position().top,
				width : this.containerDom.width(),
				height : this.containerDom.height()
			}
			this.containerOffsetInfo = {
				x : this.containerDom.offset().left,
				y : this.containerDom.offset().top,
				width : this.containerDom.width(),
				height : this.containerDom.height()
			}
			this.dataFlowInfo = {
				x : this.dataFlowDom.offset().left,
				y : this.dataFlowDom.offset().top,
				width : this.dataFlowDom.width(),
				height : this.dataFlowDom.height()
			}
		},
		/**
		 * [renderData 节点线条回填]
		 * @param  {[type]} data         [数据回填操作]
		 * @param  {[type]} containerDom [回填的dom对象]
		 */
		renderData:function(data,containerDom){
			var topThis = this;

			if(data && data.nodes){
				data.nodes.forEach(function(v,i){
					var g = v;
					topThis.drawNode({
						nodeType : g.type,
						layout:{
							class:v.className,
							id : g.frontNodeId,
							position : {x:g.x,y:g.y},
							canvasEln : containerDom,
						},
						config:v.config,
						mode:'backfill',
					});
				});
			}

			if(data && data.lines){
				data.lines.forEach(function(v,i){
					var g = v;
					topThis.drawPath({
						source : $('#'+g.fromNodeId),
						target : $('#'+g.toNodeId),
						class : v.class === undefined ? 'default':v.class,
						mode:'backfill',
					});
				});
			}
		},
		/**
		 * [initCreateFlowEvent 初始化拖拽创建流程（节点）]
		 */
		initCreateFlowEvent:function(){
			var topThis = this,
				currentNode = {},
				currentNodeInfo = {},
				isDrag = false;

			this.dataFlowDom.on('mousedown','.node-template',function(e){
				var domData = $(this).data();
				var result = true;
				topThis.getframeInfo();

				if(domData.type){
					isDrag = true;
					currentNode = topThis.drawNode({
						nodeType : domData.type,
						layout:{
							position : {
								x:e.pageX - topThis.dataFlowInfo.x - 20,
								y:e.pageY - topThis.dataFlowInfo.y - 20,
							},
							canvasEln : topThis.dataFlowDom,
						}
					});
					if(currentNode){
						currentNodeInfo = {
							width : currentNode.width(),
							height : currentNode.height(),
						}
						currentNode.css('opacity','0.4');
						if(topThis.config.hasOwnProperty("onCreateNodeAfter")){
							result = topThis.config.onCreateNodeAfter.apply(currentNode,[e]);
							result = result === true ? true :(result === undefined ? true :false);
						}
					}
				}
				if(!result){
					currentNode.remove();
					return false;
				}
			})
			.on('mousemove',function(e){
				if(isDrag && currentNode instanceof jQuery){
					currentNode.css({
						left : e.pageX - topThis.dataFlowInfo.x - currentNodeInfo.width / 4,
						top : e.pageY - topThis.dataFlowInfo.y - currentNodeInfo.height / 2,
					});
				}
			}).on('mouseup',function(e){
				var result = true;
				if(isDrag && currentNode instanceof jQuery){
					var nodeId = currentNode.prop('id');

					currentNodeInfo.x = currentNode.position().left;
					currentNodeInfo.y = currentNode.position().top;
					if(!topThis.tools().checkNodeIncontainer(currentNodeInfo,false)){
						currentNode.remove();
						delete topThis.nodesVue[nodeId];
					}else{
						var width = currentNode.width();
						var height = currentNode.height();

						var layout = {
							x : e.pageX - topThis.dataFlowInfo.x - topThis.containerInfo.x - currentNodeInfo['width'] / 4,
							y : e.pageY - topThis.dataFlowInfo.y - topThis.containerInfo.y - currentNodeInfo['height'] / 2,
						};
						var nodeVue = topThis.nodesVue[nodeId];
						nodeVue.layout.x = layout.x;
						nodeVue.layout.y = layout.y;
						currentNode.css("opacity",1);
						topThis.containerDom.append(currentNode);

						if(topThis.config.hasOwnProperty('onCreateNodeAfter')
							&& typeof topThis.config.onCreateNodeAfter ==="function"){
							var node = JSON.parse(JSON.stringify(nodeVue.$data));
							result =  topThis.config.onCreateNodeAfter(node,topThis.util().getNodes(),topThis.util().getLines());
							result = result === true ? true :(result === undefined ? true :false);
						}
					}
					isDrag = false;
				}
			})
		},
		/**
		 * [initNodeDragEvent 节点在画布中的拖拽处理/删除节点事件]
		 */
		initNodeDragEvent:function(){
			var topThis = this,
				 currentNode = {},
				 isDrag = false,
				 moveTo = {},
				 nodeInfo = {};

			topThis.containerDom.on('mousedown',".node-container",function(e){
				if(1 === e.which){
					isDrag = true;
					topThis.getframeInfo();
					currentNode = $(this).parents(".node");
					nodeInfo['width'] = currentNode.width();
					nodeInfo['height'] = currentNode.height();
					//	获取鼠标x,y 到 node 节点的左上角距离
					moveTo = {
						x : e.pageX - topThis.containerInfo.x - currentNode.position().left,
						y : e.pageY - topThis.containerInfo.y - currentNode.position().top
					}
				}else{
					isDrag = false;
				}
			})
			.on('mousemove',function(e){
				if(isDrag){
					var nodeId = currentNode.prop('id');
					var vnode = {
						x : e.pageX - topThis.containerInfo.x - moveTo.x,
						y : e.pageY - topThis.containerInfo.y - moveTo.y,
						width: currentNode.width(),
						height: currentNode.height(),
					}
					if(! topThis.tools().checkNodeIncontainer(vnode,true)){
						return false;
					}
					topThis.nodesVue[nodeId].layout.x = e.pageX - topThis.containerInfo.x - moveTo.x;
					topThis.nodesVue[nodeId].layout.y = e.pageY - topThis.containerInfo.y - moveTo.y;

					for(var e in topThis.edgesVue){
						var edge = topThis.edgesVue[e];
						var startNode = $('#'+edge.sourceId);
						var endNode = $('#'+edge.targetId);

						var offset = 10;
						var endNodeInfo = {
							x : endNode.position().left - offset / 2,
							y : endNode.position().top - offset / 2,
							width : endNode.width() + offset,
							height : endNode.height() + offset,
						}

						var startNodeInfo = {
							x : startNode.position().left - offset / 2,
							y : startNode.position().top - offset / 2,
							width : startNode.width() + offset,
							height : startNode.height() + offset,
						}

						if(nodeId === edge.targetId){

							var startPoint = topThis.tools().getConnectPoint(startNodeInfo,{
								x : endNodeInfo.x + endNodeInfo.width / 2,
								y : endNodeInfo.y + endNodeInfo.height / 2
							});
							var endPoint = topThis.tools().getConnectPoint(endNodeInfo,startPoint);

							var dString = 'M sx sy L ex ey';
							    dString = dString.replace('sx',Math.round(startPoint.x))
													  .replace('sy',Math.round(startPoint.y))
													  .replace('ex',Math.round(endPoint.x))
													  .replace('ey',Math.round(endPoint.y));
							edge.d = dString;

							var arrowPath = topThis.tools().getArrowDString(startPoint,endPoint,4);
							edge.arrowPath = arrowPath;

						}else if(nodeId === edge.sourceId){

							var startPoint = topThis.tools().getConnectPoint(startNodeInfo,{
								x : endNodeInfo.x + endNodeInfo.width / 2,
								y : endNodeInfo.y + endNodeInfo.height / 2
							});
							var endPoint = topThis.tools().getConnectPoint(endNodeInfo,startPoint);

							var dString = 'M sx sy L ex ey';
							    dString = dString.replace('sx',Math.round(endPoint.x))
													  .replace('sy',Math.round(endPoint.y))
													  .replace('ex',Math.round(startPoint.x))
													  .replace('ey',Math.round(startPoint.y));
							edge.d = dString;

							var arrowPath = topThis.tools().getArrowDString(startPoint,endPoint,4);
							edge.arrowPath = arrowPath;
						}
					}
				}
			})
			.on('mouseleave',function(e){
				isDrag = false;
			})

			topThis.dataFlowDom.on('mouseup',function(e){
				isDrag = false;
			})
			//	鼠标点击连线箭头消失。
			.on('click','#dataflow-container',function(e){
				var $dom = $(e.toElement);
				if($dom.hasClass('dataflow-container')){
					topThis.containerDom.find('.flow-link-btn').addClass('none');
				}
			})
			.on('mouseenter','#dataflow-container .line-path',function(e){
				topThis.getframeInfo();
				var tips = topThis.containerDom.find('.line-tips');
				var pointXY = {
					x:e.pageX,
					y:e.pageY,
				}
				tips.css({
					top:pointXY.y - topThis.containerOffsetInfo.y + 20,
					left:pointXY.x - topThis.containerOffsetInfo.x + 20,
				});
				tips.removeClass('none');
			})
			.on('mouseleave','#dataflow-container .line-path',function(e){
				var tips = topThis.containerDom.find('.line-tips');
				tips.addClass('none');
			}).on('dblclick','.line-path',function(e){
				topThis.util().remove({
					type:'path',
					eln:$(this)
				});
			});

			//快捷键
			// (function(){
			// 	var choose = {};
			// 	var pointXY = {x:0,y:0};
			// 	var copyId = undefined;

			// 	// .on('click','#dataflow-container .line-path,#dataflow-container .node',function(){
			// 	// 	var $this = $(this);
			// 	// 	if($this.hasClass('node')){
			// 	// 		choose.type = "node";
			// 	// 	}else{
			// 	// 		choose.type = "path";
			// 	// 	}
			// 	// 	pointXY = {
			// 	// 		y: $this.position().top + 100,
			// 	// 		x: $this.position().left + 100,
			// 	// 	}
			// 	// 	choose.eln = $this;
			// 	// })
			// 	// .on('keydown',function(e){
			// 	// 	// if(46 === e.keyCode){
			// 	// 	// 	if(choose.type !== undefined){
			// 	// 	// 		e.preventDefault();
			// 	// 	// 		topThis.temp().remove(choose);
			// 	// 	// 	}
			// 	// 	// }
			// 	// 	// ctrl+c
			// 	// 	if(choose.type !== undefined &&(e.ctrlKey === true && 67 === e.keyCode)){
			// 	// 		copyId = choose.eln.prop('id');
			// 	// 	}
			// 	// 	// ctrl+v
			// 	// 	if(copyId != undefined &&(e.ctrlKey === true && 86 === e.keyCode)){
			// 	// 		var copyNode = topThis.nodesVue[copyId];
			// 	// 		var cId = copyId;
			// 	// 		if(copyNode.config && copyNode.config.copyId){
			// 	// 			cId = copyNode.config.copyId;
			// 	// 		}
			// 	// 		topThis.drawNode({
			// 	// 			nodeType : copyNode.type,
			// 	// 			layout:{
			// 	// 				position : pointXY,
			// 	// 			},
			// 	// 			config:{
			// 	// 				copyId:cId
			// 	// 			}
			// 	// 		});
			// 	// 		cId = undefined;
			// 	// 		copyId = undefined;
			// 	// 	}
			// 	// })
			// 	// .on('mouseleave','#dataflow-container .node,#dataflow-container .line-path',function(e){
			// 	// 	choose = {};
			// 	// })
			// 	// .on('mousemove','#dataflow-container',function(e){
			// 	// 	pointXY ={
			// 	// 		x:e.pageX - topThis.containerOffsetInfo.x - 20,
			// 	// 		y:e.pageY - topThis.containerOffsetInfo.y - 20
			// 	// 	}
			// 	// })
			// }())
		},
		/**
		 * [initConnectionEvent 鼠标连线操作]
		 */
		initConnectionEvent:function(){
			var isDrag = false;
			var startPosition = {};		//	线条的开始节点的中心点
			var currNodeInfo = {};		//	当前节点的位置信息
			var path = {};					//	路径对象
			var topThis = this;
			var sourceId = {};
			var sourceNode = {};
			var checkedNode = {};

			topThis.containerDom.on('click','.node-container',function(e){
				// e.stopPropagation();
				// e.preventDefault();
				var _This = $(this);
				topThis.getframeInfo();
				topThis.containerDom.find('.flow-link-btn').addClass('none');
				_This.siblings('.flow-link-btn').removeClass('none');

				checkedNode = {
					isChecked : true,
					node : _This,
				}
			})
			.on('mousedown','.flow-link',function(e){
				var node = $(this).parents('.node');
				sourceId = node.prop('id');
				sourceNode = node;

				currNodeInfo = {
					x : node.position().left,
					y : node.position().top,
					height : node.height(),
					width : node.width(),
					id : sourceId,
				}

				var centerX = currNodeInfo.x + currNodeInfo.width / 2;
				var centerY = currNodeInfo.y + currNodeInfo.height / 2;

				startPosition.x = centerX;
				startPosition.y = centerY;
				startPosition.id = sourceId;
				path = topThis.drawPath({source : node, target : node ,class:'default',mode:'backfill'});
				isDrag = true;
			})
			.on('mouseup',".node-container",function(e){
				if(isDrag){
					var targetNode = $(this).parents('.node');

					var targetNodeInfo = {
						x : targetNode.position().left,
						y : targetNode.position().top,
						height : targetNode.height(),
						width : targetNode.width(),
						id : targetNode.prop('id'),
					};

					topThis.drawPath({
						source : sourceNode,
						target : targetNode,
						class:'default',
					});
					sourceNode.find('.flow-link-btn').addClass('none');
					checkedNode.isChecked = false;
				}
			})
			.on('mouseup',function(e){
				if(isDrag && path){
					isDrag = false;
					var svgDom = path.eln.parents('svg');
					svgDom.remove();
					delete topThis.edgesVue[svgDom.prop('id')];
					currNodeInfo = [];
					startPosition = [];
				}
			})
			.on('mousemove',function(e){
				if(isDrag && path){
					var endPosition = [];
					endPosition['x'] = Math.round(e.pageX - topThis.dataFlowInfo.x - topThis.containerInfo.x);
					endPosition['y'] = Math.round(e.pageY - topThis.dataFlowInfo.y - topThis.containerInfo.y);
					var d = 'M sx sy L ex ey';
					d = d.replace('sy',startPosition["y"])
						  .replace('sx',startPosition['x'])
						  .replace('ex',endPosition['x'])
						  .replace('ey',endPosition['y']);
					path.eln.attr('d',d);
				}
			})
		},
		/**
		 * [drawPath 绘制路径]
		 * @param  {[object]} options.source   [起点节点信息]
		 * @param  {[object]} options.target   [目标节点信息]
		 * @return {[object]}       [jquery的路径对象]
		 */
		drawPath:function(options){
			var topThis = this;
			var isExist = false;
			var offset = 15;
			var sourceNode = options.source;
			var targetNode = options.target;

			var sourceNodeId = sourceNode.prop('id');
			var targetNodeId = targetNode.prop('id');
			var callbackResult = true;

			this.getframeInfo();

			if('backfill' !== options.mode && this.config.hasOwnProperty('onCreateLineBefore')
				&& typeof this.config.onCreateLineBefore ==="function"){
				var eln = {source:sourceNode,target:targetNode};
				var info =  {source:topThis.nodesVue[sourceNodeId], target:topThis.nodesVue[targetNodeId]};
				callbackResult = this.config.onCreateLineBefore(eln,info);
				callbackResult = callbackResult === true ? true :(callbackResult === undefined ? true :false);
			}
			if(!callbackResult){
				return false;
			}

			var sourceInfo={
				id : sourceNodeId,
				x : sourceNode.position().left,
				y : sourceNode.position().top,
				width : sourceNode.width(),
				height :  sourceNode.height(),
			}

			var targetInfo={
				id : targetNodeId,
				x : targetNode.position().left,
				y : targetNode.position().top,
				width : targetNode.width(),
				height :  targetNode.height(),
			}

			//	连接模式计算位置并且计算是否有重复连接的线条
			sourceInfo.x  = sourceInfo.x - offset / 2;
			sourceInfo.y  = sourceInfo.y - offset / 2;
			sourceInfo.width  = sourceInfo.width + offset;
			sourceInfo.height = sourceInfo.height + offset;

			targetInfo.x  = targetInfo.x - offset / 2;
			targetInfo.y  = targetInfo.y - offset / 2;
			targetInfo.width  = targetInfo.width + offset;
			targetInfo.height = targetInfo.height + offset;

			var startPoint = topThis.tools().getConnectPoint(sourceInfo,{
				x : targetInfo.x + targetInfo.width / 2 ,
				y : targetInfo.y + targetInfo.height / 2 ,
			});
			var endPoint = topThis.tools().getConnectPoint(targetInfo,startPoint);

			sourceInfo.x = startPoint.x;
			sourceInfo.y = startPoint.y;

			targetInfo.x = endPoint.x;
			targetInfo.y = endPoint.y;

			var lines = topThis.util().getLines();

			lines.forEach(function(v){
				if(!isExist && v.sourceId === sourceInfo.id && v.targetId === targetInfo.id){
					if(topThis.config.dialog){
						topThis.config.dialog({
							type:'info',
							msg:'已连接过此节点',
						})
					}else{
						alert('已连接过此节点');
					}
					isExist = true;
				}
			})

			if( !isExist){
				var uuuid = topThis.tools().getUUid().substr(-5);
				var pathId = "path_"+uuuid;
				var arrowPath = topThis.tools().getArrowDString(sourceInfo,targetInfo,4);

				var svgObj = $('<svg>'+
			      	'<path class="line-path" :class="class" :data-id="id" :d="d" :stroke="color"></path>'+
			      	'<path class="arrow-path" :class="class" :data-id="id" :d="arrowPath"></path>'+
			   	'</svg>'
				)

			   svgObj.prop("id",pathId);
			   if(options.canvasEln && options.canvasEln.length == 1){
			   		options.canvasEln.append(svgObj);
			   }else{
			   		this.containerDom.append(svgObj);
			   }

			   var dString = 'M sx sy L ex ey';
			   dString = dString.replace('sx',Math.round(sourceInfo["x"]))
									  .replace('sy',Math.round(sourceInfo["y"]))
									  .replace('ex',Math.round(targetInfo['x']))
									  .replace('ey',Math.round(targetInfo['y']));

			   var pathObj  = new Vue({
				  	el: '#'+pathId,
				  	data: {
				   	id:pathId,
				   	d:dString,
				   	startPosition:{
				   		x : Math.round(sourceInfo.x),
				   		y : Math.round(sourceInfo.y),
				   		width : sourceInfo.width,
				   		height : sourceInfo.height
				   	},
				   	endPosition:{
				   		x:Math.round(sourceInfo.x),
				   		y:Math.round(sourceInfo.y),
				   		width:targetInfo && targetInfo.width ? targetInfo.width : null,
				   		height:targetInfo && targetInfo.height ? targetInfo.height : null
				   	},
				   	class: options.class,
				   	sourceId : sourceInfo && sourceInfo.id !== undefined ? sourceInfo.id : null,
				   	arrowPath : arrowPath,
				   	targetId : targetInfo && targetInfo.id !== undefined ? targetInfo.id : null,
				  	}
				});

			   	//	是否写入缓存
				options.saveTocache = options.saveTocache == undefined ? true : false;
				if(options.saveTocache){
					topThis.edgesVue[pathId] = pathObj;
				}

				// topThis.nodesVue[sourceNodeId].targetInfo.push({
				// 	nodeId : targetNodeId,
				// 	pathId : pathId
				// });
				// topThis.nodesVue[targetNodeId].sourceInfo.push({
				// 	nodeId : sourceNodeId,
				// 	pathId : pathId
				// });

				if('backfill' !== options.mode && this.config.hasOwnProperty('onCreateLineAfter')
					&& typeof this.config.onCreateLineAfter ==="function"){
					var eln = {source:sourceNode,target:targetNode,};
					var info =  {source:topThis.nodesVue[sourceNodeId], target:topThis.nodesVue[targetNodeId],line:pathObj};
					callbackResult = this.config.onCreateLineAfter(eln,info);
					callbackResult = callbackResult === true ? true :(callbackResult === undefined ? true :false);
					if(callbackResult === undefined){
						callbackResult = true;
					}
				}
				return {id : pathId , eln : svgObj.find('path')};
			}else{
				return {isExist:isExist};
			}
		},
		/**
		 * [drawNode 根据传入的参数绘制节点]
		 * @param  {[string]} nodeType [节点类型]
		 * @param  {[object]} position [位置信息]
		 * @param  {[string]} id [节点ID,若ID为空则表示新增.否则是回填]
		 * @param  {[object]} canvasEln [将节点绘制的画布节点。]
		 * @return {[jQuery object]}          [description]
		 */
		drawNode:function(options){
			var nodeType = options.nodeType;
			var position = options.layout.position;
			var id = options.layout.id;
			var beforeResult = true;
			this.getframeInfo();
			if('backfill' !== options.mode && this.config.hasOwnProperty('onCreateNodeBefore')
				&& typeof this.config.onCreateNodeBefore ==="function"){
				beforeResult = this.config.onCreateNodeBefore(options,this.util().getNodes(),this.util().getLines());
				beforeResult = beforeResult === true ? true :(beforeResult === undefined ? true :false);
			}
			if(!beforeResult){
				return false;
			}
			if(nodeType && typeof nodeType ==="string"){
				var topThis = this,
					nodeId = id === undefined ? "node_"+topThis.tools().getUUid().substr(-5) : id,
					currentNode = {},
					currentNodeInfo={};
				currentNode = $(topThis.getNodeTemplate(nodeType));
				currentNode.prop("id",nodeId);

				currentNodeInfo['width'] = currentNode.width();
				currentNodeInfo['height'] = currentNode.height();

		 		var top = position.x - currentNodeInfo['width'] / 4;
		 		var left = position.y - currentNodeInfo['height'] / 2;

		 		if(options.layout.canvasEln && options.layout.canvasEln.length == 1){
		 			options.layout.canvasEln.append(currentNode);
		 		}else{
		 			topThis.containerDom.append(currentNode);
		 		}
				var vue_currNode = new Vue({
				  	el: '#'+nodeId,
				  	data:{
				  		id:nodeId,
				  		type :nodeType,
				  		checked:false,
				  		config : options.config,
				  		layout:{
				  			x : position.x,
				  			y : position.y,
				  			// width:currentNode.width(),
				  			// height:currentNode.height(),
				  			class:options.layout.class === undefined ? 'invalid':options.layout.class,
				  		},
				  		// sourceInfo :[],
				  		// targetInfo :[]
				  	},
				});

				//	是否写入缓存
				options.saveTocache = options.saveTocache == undefined ? true : false;
				if(options.saveTocache){
					topThis.nodesVue[nodeId] = vue_currNode;
				}

		 		currentNode.removeClass('none');
		 		return currentNode;
			}else{
				return false;
			}
		},
		/**
		 * [getNodeTemplate 根据传入ID返回模板节点]
		 * @param  {[string]} nodeType [模板ID]
		 * @return {[object]}              [模板节点]
		 */
		getNodeTemplate:function(nodeType){
			var topThis = this,
				templateHtml = topThis.templateDom.find('[data-type="'+nodeType+'"]').clone();
			if(templateHtml.length ===1){
				return templateHtml[0];
			}
		},

		tools:function(){
			var topThis = this;
			return {
				/**
				 * [getUUid 生成UUID]
				 * @return {[string]} [返回UUID]
				 */
				getUUid:function(){
					var s = [];
				   var hexDigits = "0123456789abcdef";
				   for (var i = 0; i < 36; i++) {
				       s[i] = hexDigits.substr(Math.floor(Math.random() * 0x10), 1);
				   }
				   s[14] = "4";
				   s[19] = hexDigits.substr((s[19] & 0x3) | 0x8, 1);
				   s[8] = s[13] = s[18] = s[23] = "_";
				   return s.join("");
				},

				/**
				 * [getArrowDString 获取箭头的path 的　"d" 字符串]
				 * @param  {[type]} l [开始节点]
				 * @param  {[type]} k [结束节点]
				 * @param  {[type]} d [箭头大小]
				 * @return {[type]}   [description]
				 */
				getArrowDString: function(l, k, d) {
					var g = Math.atan2(l.y - k.y, k.x - l.x) * (180 / Math.PI);
					var h = k.x - d * Math.cos(g * (Math.PI / 180));
					var f = k.y + d * Math.sin(g * (Math.PI / 180));
					var e = h + d * Math.cos((g + 120) * (Math.PI / 180));
					var j = f - d * Math.sin((g + 120) * (Math.PI / 180));
					var c = h + d * Math.cos((g + 240) * (Math.PI / 180));
					var i = f - d * Math.sin((g + 240) * (Math.PI / 180));

					var arrowPosition = [k, {x: e, y: j }, {x: c, y: i }];

					var arrowPath = "M" + arrowPosition[0].x + " " + arrowPosition[0].y + "L" + arrowPosition[1].x + " " + arrowPosition[1].y + "L" + arrowPosition[2].x + " " + arrowPosition[2].y + "z";
					return arrowPath;
				},
				getConnectPoint: function(j, d) {
					var c = d,
					e = {
						x: j.x + j.width / 2,
						y: j.y + j.height / 2
					};
					var l = (e.y - c.y) / (e.x - c.x);
					l = isNaN(l) ? 0 : l;
					var k = j.height / j.width;
					var h = c.y < e.y ? -1 : 1,
					f = c.x < e.x ? -1 : 1,
					g,
					i;
					if (Math.abs(l) > k && h == -1) {
						g = e.y - j.height / 2;
						i = e.x + h * j.height / 2 / l
					} else {
						if (Math.abs(l) > k && h == 1) {
							g = e.y + j.height / 2;
							i = e.x + h * j.height / 2 / l
						} else {
							if (Math.abs(l) < k && f == -1) {
								g = e.y + f * j.width / 2 * l;
								i = e.x - j.width / 2
							} else {
								if (Math.abs(l) < k && f == 1) {
									g = e.y + j.width / 2 * l;
									i = e.x + j.width / 2
								}
							}
						}
					}
					var position = {
						x: i,
						y: g,
					};
					return position;
				},
				/**
				 * [checkNodeIncontainer 检查节点是否在画布容器范围内]
				 * @param  {[type]} currentNode [节点对象的长宽坐标信息]
				 * @return {[boolean]}             [是否在画布内]
				 */
				checkNodeIncontainer:function(nodeInfo,nodeInfoInBox){
					topThis.getframeInfo();
					if(nodeInfoInBox){
						nodeInfo.x = nodeInfo.x + topThis.containerInfo.x;
						nodeInfo.y = nodeInfo.y + topThis.containerInfo.y;
					}
					if(nodeInfo.x < topThis.containerInfo.x
						|| nodeInfo.x + nodeInfo.width > topThis.containerInfo.width +topThis.containerInfo.x
						|| nodeInfo.y < topThis.containerInfo.y
						|| nodeInfo.height + nodeInfo.y > topThis.containerInfo.height +topThis.containerInfo.y){
						return false;
					}
					else{
						return true;
					}
				}
			}
		},
		/**
		 * [temp 对外暴露的方法]
		 * @return {[type]} [description]
		 */
		util:function(){
			var topThis = this;
			return {
				/**
				 * [getNodes 获取所有的节点信息]
				 * @return {[array]} [节点数组]
				 */
				getNodes:function(){
					var nodes = topThis.nodesVue;
					var nodesArray = [];
					for(var id in nodes){
						var node = nodes[id];
						nodesArray.push(JSON.parse(JSON.stringify(node.$data)));
					}
					return nodesArray;
				},
				/**
				 * [getLines 返回所有的线条数据]
				 * @return {[Array]} [线条对象数组]
				 */
				getLines:function(){
					var lines = topThis.edgesVue;
					var linesArray = [];
					for(var id in lines){
						var line = lines[id];
						var lineObj = JSON.parse(JSON.stringify(line.$data));
						linesArray.push({
							id:lineObj.id,
							sourceId: lineObj.sourceId,
							targetId:lineObj.targetId,
							class:lineObj.class,
						});
					}
					return linesArray;
				},
				/**
				 * [remove 根据传入的参数删除节点]
				 * @param  {[type]} options.type [要删除的类型可选为“node”,"path"]
				 * @param  {[type]} options.eln  [要删除的jquery dom对象]
				 * @return {[type]}         [description]
				 */
				remove:function(options){
					if(options.hasOwnProperty('type') && options.hasOwnProperty('eln')){
						var eln = options.eln;
						var result = true;
						if(topThis.config.hasOwnProperty('onRemoveBefore')
							&& typeof topThis.config.onRemoveBefore ==="function"){
							result = topThis.config.onRemoveBefore(options);
							result = result === true ? true :(result === undefined ? true :false);
						}
						if(!result){
							return false;
						}
						if("node" === options.type){
							var id = eln.prop('id');
							var node = topThis.nodesVue[id];
							var edge = topThis.util().getLines();
							edge.forEach(function(v,i){
								if(node.id === v.sourceId || node.id === v.targetId){
									delete topThis.edgesVue[v.id];
									$('#'+v.id).remove();
								}
							});
							$('#'+node.id).remove();
							delete topThis.nodesVue[node.id];
						}else{
							var id = eln.data('id');
							eln.parents('svg').remove();
							delete topThis.edgesVue[id];
						}
					}else{
						console.error('参数错误');
					}
					topThis.containerDom.find('.line-tips').addClass('none');
				},
				getLinesByNodeId:function(nodeId,type){
					var lines = this.getLines();
					return lines.filter(function(v,i) {
						if("source" == type && nodeId == v.targetId){
							return v;
						}else if("target" === type && nodeId === v.sourceId){
							return v;
						}
					});
				}
			}
		}
	}
	/**
	 * [workFlow 将dataFlow拓展成jquery插件]
	 * @param  {[type]} config [配置项]
	 * @return {[type]}        [description]
	 */
	$.fn.workFlow = function(config){
		var dataFlowConfig = config ? config : {};
		dataFlowConfig.dataFlowDom = this;
		var dataFlow = new DataFlow(dataFlowConfig);
		return {
			/**
			 * [getNodeVueById 根据ID返回节点的Vue对象]
			 * @param  {[string]} id [节点ID]
			 * @return {[object]}    [vue对象]
			 */
			getNodeVueById:function(id){
				return dataFlow.nodesVue[id];
			},

			/**
			 * [getLineVueById 根据ID返回线条的Vue对象]
			 * @param  {[string]} id [线条ID]
			 * @return {[object]}    [vue对象]
			 */
			getLineVueById:function(id){
				return dataFlow.edgesVue[id];
			},

			//	[getLines 获取所有的节点信息]
			getNodes:function(){
				return dataFlow.util().getNodes();
			},

			//	[getLines 获取所有的线条信息]
			getLines:function(){
				return dataFlow.util().getLines();
			},

			/**
			 * [getLinesByNodeId 根据节点ID返回线条信息]
			 * @param  {[string]} noeId [节点ID]
			 * @param  {[string]} type  [线条类型] 可选：source/target
			 * @return {[array]}       [description]
			 */
			getLinesByNodeId:function(noeId,type){
				return dataFlow.util().getLinesByNodeId(noeId,type);
			},

			/**
			 * [drawNode 根据传入的参数绘制节点]
			 * @param  {[string]} nodeType [节点类型]
			 * @param  {[object]} position [位置信息]
			 * @param  {[string]} id [节点ID,若ID为空则表示新增.否则是回填]
			 * @return {[jQuery object]}          [description]
			 * @example
			 * topThis.drawNode({
					nodeType : "realtime",				//类型
					layout:{
						id : g.frontNodeId,				//ID,不填则自动生成ID
						position : {x:100,y:200},		//坐标
						canvasEln : containerDom,		//画布对象，不填则使用默认画布
					},
					config:v.conf1,						//配置对象，直接存储在vue的config中。
				});
			 *
			 */
			drawNode:function(options){
				return dataFlow.drawNode(options);
			},
			/**
			 * [drawPath 对外暴露的新增线条方法]
			 * @param  {[jQuery Object]} options.source [开始节点对象]
			 * @param  {[jQuery Object]} options.target [结束节点对象]
			 * @return {[jQuery Object]}         		[线条对象]
			 * @example [drawPath({source:$('#a1'),target:$('#a2')})]
			 */
			drawPath:function(options){
				return dataFlow.drawPath(options);
			},
			/**
			 * [remove 删除节点和线条]
			 * @param  {[type]} options [description]
			 * @return {[type]}         [description]
			 */
			remove:function(options){
				return dataFlow.util().remove(options);
			},
			setDrag:function(drag){
				if("boolean" === typeof drag){
					dataFlow.config.drag = drag;
				}
			}
		}
	}
}(jQuery))
