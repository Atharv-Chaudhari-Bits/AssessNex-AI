import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

// Render an HTML element to a PDF Blob using html2canvas + jsPDF
export async function renderElementToPdfBlob(element, options = {}){
  const { unit = 'pt', format = 'a4', scale = 2, margin = 20 } = options
  // use html2canvas to render element
  const canvas = await html2canvas(element, { scale, useCORS: true, logging: false })
  const imgData = canvas.toDataURL('image/png')
  const pdf = new jsPDF({ unit, format })
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()

  // Calculate dimensions to fit width
  const imgProps = { width: canvas.width, height: canvas.height }
  const ratio = Math.min(pageWidth / imgProps.width, pageHeight / imgProps.height)
  const imgWidth = imgProps.width * ratio
  const imgHeight = imgProps.height * ratio

  pdf.addImage(imgData, 'PNG', margin, margin, imgWidth - margin * 2, imgHeight - margin * 2)

  // return blob
  const blob = pdf.output('blob')
  return blob
}

export async function downloadBlob(blob, filename = 'document.pdf'){
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
