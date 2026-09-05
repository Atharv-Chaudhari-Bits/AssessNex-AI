import React, {useState} from 'react'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'

function reorder(list, startIndex, endIndex) {
  const result = Array.from(list)
  const [removed] = result.splice(startIndex, 1)
  result.splice(endIndex, 0, removed)
  return result
}

export default function DragDropBuilder({initial = [], onSave}){
  const [items, setItems] = useState(initial)

  const onDragEnd = (result) => {
    if (!result.destination) return
    const reordered = reorder(items, result.source.index, result.destination.index)
    setItems(reordered)
  }

  return (
    <div className="card p-4">
      <DragDropContext onDragEnd={onDragEnd}>
        <Droppable droppableId="q-list">
          {(provided)=> (
            <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-2">
              {items.map((it, idx)=> (
                <Draggable key={it.id} draggableId={String(it.id)} index={idx}>
                  {(prov)=> (
                    <div ref={prov.innerRef} {...prov.draggableProps} {...prov.dragHandleProps} className="p-3 bg-white rounded shadow-sm flex items-center justify-between">
                      <div className="text-sm">{it.text}</div>
                      <div className="text-xs text-muted">Drag</div>
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
      <div className="mt-4 flex justify-end">
        <button onClick={()=>onSave && onSave(items)} className="px-4 py-2 bg-primary text-white rounded">Save Exam</button>
      </div>
    </div>
  )
}
