# Architecture: Document-Based Question Generation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GeneratePage Component                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ TAB 1: 📄 Document-Based                TAB 2: ⚙️ Manual            │   │
│  │ ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │ │  DocumentChatBox Component                                      │ │   │
│  │ │  ┌────────────────────────────────────────────────────────────┐ │ │   │
│  │ │  │ 📤 Upload / 📝 Paste Document                            │ │ │   │
│  │ │  ├────────────────────────────────────────────────────────────┤ │ │   │
│  │ │  │ 💬 Chat Messages                                          │ │ │   │
│  │ │  │ ┌──────────────────────────────────────────────────────┐ │ │ │   │
│  │ │  │ │ System: Document loaded (2,456 words)              │ │ │ │   │
│  │ │  │ │ User:   Generate 5 multiple choice questions      │ │ │ │   │
│  │ │  │ │ AI:     Generated Q1, Q2, Q3...                  │ │ │ │   │
│  │ │  │ └──────────────────────────────────────────────────┘ │ │ │ │   │
│  │ │  ├────────────────────────────────────────────────────────┤ │ │ │   │
│  │ │  │ Settings:                                             │ │ │ │   │
│  │ │  │ Subject: [Machine Learning ▼]                         │ │ │ │   │
│  │ │  │ Type:    [Multiple Choice ▼]                          │ │ │ │   │
│  │ │  │ Diff:    [Medium ▼]                                   │ │ │ │   │
│  │ │  ├────────────────────────────────────────────────────────┤ │ │ │   │
│  │ │  │ 📨 Message: _________________ [→ Send]               │ │ │ │   │
│  │ │  └────────────────────────────────────────────────────────┘ │ │ │   │
│  │ │                                                              │ │ │   │
│  │ │  Quick Actions                                              │ │ │   │
│  │ │  [👁️ Preview] [📥 Download] [📧 Email]                    │ │ │   │
│  │ └────────────────────────────────────────────────────────────┘ │ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/JSON
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API SERVICE LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  axios instance: baseURL = 'http://localhost:8000/api/v1'                   │
│                                                                              │
│  api.documents = {                                                          │
│    parsePdf(file)             → POST /documents/parse-pdf                   │
│    parseDocx(file)            → POST /documents/parse-docx                  │
│    generateQuestions(...)     → POST /documents/generate-questions          │
│    summarize(text)            → POST /documents/summarize                   │
│    extractConcepts(text)      → POST /documents/extract-concepts            │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP Request
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND API LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  FastAPI Router: documents.py (Prefix: /api/v1/documents)                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /parse-pdf                                                    │   │
│  │ ├─ Validate: File type, size                                     │   │
│  │ ├─ Parse: PyPDF2.PdfReader(file)                                 │   │
│  │ ├─ Extract: Text from all pages                                  │   │
│  │ └─ Return: { text, word_count, page_count, status }              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /parse-docx                                                   │   │
│  │ ├─ Validate: File type, size                                     │   │
│  │ ├─ Parse: docx.Document(file)                                    │   │
│  │ ├─ Extract: Text from all paragraphs                             │   │
│  │ └─ Return: { text, word_count, status }                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /generate-questions                                           │   │
│  │ ├─ Input:  document_text, question_prompt, subject, type, etc.   │   │
│  │ ├─ Process:                                                       │   │
│  │ │  1. Validate inputs                                            │   │
│  │ │  2. Get QuestionGenerationAgent                               │   │
│  │ │  3. Combine document + prompt into context                    │   │
│  │ │  4. Call agent.generate_questions(context)                    │   │
│  │ │  5. Format response                                            │   │
│  │ │  6. Return questions                                           │   │
│  │ └─ Return: { data: [questions], metadata }                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /summarize                                                    │   │
│  │ ├─ Call LLM: "Summarize this in 500 words"                        │   │
│  │ └─ Return: { summary, metadata }                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /extract-concepts                                             │   │
│  │ ├─ Call LLM: "Extract key concepts as JSON"                       │   │
│  │ └─ Return: { concepts, metadata }                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ QuestionGeneration   │  │    Other Agents     │  │   Utility Functions   │
│      Agent           │  │                      │  │                       │
│                      │  │ - PlagiarismAgent    │  │ - format_questions()  │
│ ├─ generate_q's()    │  │ - PaperAgent        │  │ - fix_latex()         │
│ ├─ validate()        │  │ - FormattingAgent   │  │ - validate_input()    │
│ └─ format()          │  │                      │  │ - get_logger()        │
│                      │  │                      │  │                       │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘
        │                           │                         │
        └───────────────┬───────────┴──────────────┬──────────┘
                        │                          │
                        ▼                          ▼
            ┌────────────────────┐     ┌──────────────────────┐
            │  LLM Provider      │     │  Document Storage    │
            │                    │     │                      │
            │ - Azure OpenAI     │     │ - Session State      │
            │ - Google GenAI     │     │ - Component State    │
            │ - Groq            │     │ - Browser LocalStore │
            │ - Grok            │     │                      │
            └────────────────────┘     └──────────────────────┘
```

---

## Component Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      GeneratePage                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  state: questions, activeTab, docInfo, loading             │ │
│  │  methods: handleQuestionsGenerated(), handleDocumentLoaded()
│  └────────────────────────────────────────────────────────────┘ │
│                         │                                        │
│         ┌───────────────┼───────────────┐                        │
│         │               │               │                        │
│         ▼               ▼               ▼                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────┐          │
│  │  Sidebar   │  │  Navbar    │  │ DocumentChatBox  │ (NEW)    │
│  └────────────┘  └────────────┘  │ ┌──────────────┐ │          │
│                                   │ │ state: ...   │ │          │
│                                   │ │ methods: ... │ │          │
│                                   │ └──────────────┘ │          │
│                                   └──────────────────┘          │
│                                         │                       │
│                                         │ onQuestionsGenerated()
│                                         │ onDocumentLoaded()    │
│                                         ▼                       │
│                                   setQuestions()                │
│                                   setDocInfo()                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INPUT: User File/Text                                   │
└──────────────────────┬──────────────────────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
  ┌──────────┐               ┌────────────────┐
  │PDF/DOCX  │               │  Paste Text    │
  │  File    │               │   (String)     │
  └────┬─────┘               └────┬───────────┘
       │                          │
       │ POST /parse-pdf          │ POST /generate-questions
       │ or /parse-docx           │ (with text directly)
       │                          │
       └──────────────┬───────────┘
                      │
                      ▼
       ┌────────────────────────────────────┐
       │ Backend Processing                 │
       │ ┌──────────────────────────────────┐
       │ │ 1. Extract/Parse Text           │
       │ │ ├─ PyPDF2 for PDF               │
       │ │ ├─ python-docx for DOCX         │
       │ │ └─ Direct use for text          │
       │ └──────────────────────────────────┘
       │ ┌──────────────────────────────────┐
       │ │ 2. Combine with User Prompt     │
       │ │ ├─ Document text                │
       │ │ ├─ Question prompt from user    │
       │ │ └─ Configuration (subject, etc) │
       │ └──────────────────────────────────┘
       │ ┌──────────────────────────────────┐
       │ │ 3. Call LLM                     │
       │ │ ├─ QuestionGenerationAgent      │
       │ │ └─ With enhanced context        │
       │ └──────────────────────────────────┘
       │ ┌──────────────────────────────────┐
       │ │ 4. Format Response              │
       │ │ ├─ Add metadata                 │
       │ │ ├─ Validate questions           │
       │ │ └─ Return structured JSON       │
       │ └──────────────────────────────────┘
       └──────────────┬────────────────────┘
                      │
                      ▼
       ┌────────────────────────────────────┐
       │ Response: Questions with Metadata  │
       │ {                                  │
       │   status: "success",               │
       │   data: [ {...question...}, ... ], │
       │   metadata: {...}                  │
       │ }                                  │
       └──────────────┬────────────────────┘
                      │
                      ▼
       ┌────────────────────────────────────┐
       │ Frontend Display                   │
       │ ├─ Show in chat                    │
       │ ├─ Display in sidebar              │
       │ ├─ Enable export options           │
       │ └─ Store in state                  │
       └────────────────────────────────────┘
```

---

## State Management Flow

```
User Interaction → Frontend State Update → Re-render UI

├─ Upload Document
│  └─ setDocument({ name, type, text, uploadedAt, wordCount })
│     └─ Show in chat: "Document loaded"
│
├─ Ask Question
│  ├─ setMessages([...messages, { type: 'user', content }])
│  ├─ API Call: generateQuestions()
│  └─ On Response:
│     ├─ setMessages([...messages, { type: 'assistant', questions }])
│     └─ setGeneratedQuestions(questions)
│
├─ Change Settings
│  ├─ setSubject(value)
│  ├─ setQuestionType(value)
│  └─ setDifficulty(value)
│
├─ Export
│  ├─ Copy: navigator.clipboard.writeText()
│  ├─ Download: generatePDF() → downloadBlob()
│  └─ Email: api.sendEmail()
│
└─ Clear
   ├─ setMessages([])
   └─ setDocument(null)
```

---

## Error Handling Flow

```
API Request
    │
    ├─ Client-side Validation
    │  ├─ File type check
    │  ├─ File size check
    │  └─ Content validation
    │
    ▼
Backend Request
    │
    ├─ Server-side Validation
    │  ├─ Input schema validation (Pydantic)
    │  ├─ File format validation
    │  └─ Content length check
    │
    ├─ Processing
    │  ├─ PDF/DOCX parsing
    │  ├─ Text extraction
    │  └─ LLM API calls
    │
    ├─ Error Cases
    │  ├─ Invalid file → HTTP 400
    │  ├─ File too large → HTTP 413
    │  ├─ Parse error → HTTP 400
    │  ├─ LLM timeout → HTTP 504
    │  └─ Server error → HTTP 500
    │
    ▼
Response with Error Details
    │
    ├─ HTTPException(status_code, detail)
    │  └─ Returns: { "detail": "Human-readable error message" }
    │
    ▼
Frontend Error Handling
    │
    ├─ Check response.ok
    │  ├─ Success → Process data
    │  └─ Error → Show toast.error()
    │
    ├─ Add error message to chat
    │  └─ type: 'error', content: error message
    │
    └─ Log to console
       └─ console.error(error)
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ React 18                    - UI Framework                       │
│ Vite                        - Build tool                         │
│ Axios                       - HTTP client                        │
│ TailwindCSS                 - Styling                            │
│ Framer Motion               - Animations                         │
│ react-hot-toast             - Notifications                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                         HTTP/REST
                              │
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ FastAPI 0.124.4             - Web framework                      │
│ Uvicorn 0.38.0              - ASGI server                        │
│ Pydantic                    - Data validation                    │
│ python-multipart            - File upload support               │
│ PyPDF2 4.0.1                - PDF parsing                        │
│ python-docx 0.8.11          - DOCX parsing                       │
│ LangChain                   - LLM framework                      │
│ LangGraph                   - Workflow orchestration            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                         LLM API
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LLM PROVIDER LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Azure OpenAI (Default)      - GPT-4, GPT-3.5                    │
│ Google GenAI                - Gemini                            │
│ Groq                        - LLaMA 2                           │
│ Grok (X API)                - Grok                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

```
Development
├─ Frontend Dev Server: http://localhost:5173
├─ Backend Dev Server: http://localhost:8000
└─ Hot reload enabled

Production
├─ Frontend
│  ├─ Build: npm run build
│  ├─ Output: dist/
│  └─ Serve: Static hosting (Vercel, Netlify, S3)
│
└─ Backend
   ├─ Docker container or direct uvicorn
   ├─ Environment: production
   ├─ CORS: Production domains
   └─ Logging: Production-grade logging
```

---

## Performance Metrics

```
Operation                   Time Range      Notes
─────────────────────────────────────────────────────────────
Upload PDF (1-5MB)         1-3 seconds     Depends on file size
Upload DOCX (1-5MB)        0.5-2 seconds   Usually faster than PDF
Text Paste                 Instant         No processing needed
Parse PDF/DOCX             0.5-3 seconds   Text extraction
Question Generation        3-8 seconds     Per 5 questions
Chat Message Display       Instant         Client-side rendering
PDF Export                 1-2 seconds     Client-side
Email Send                 1-2 seconds     Backend processing
```

---

## Security Considerations

```
Input Validation
├─ File type whitelist: .pdf, .docx, .txt
├─ File size limit: 10MB
├─ Content length validation
└─ Sanitize user input

API Security
├─ CORS enabled for frontend origin
├─ Request size limits
├─ Rate limiting (recommended)
└─ Error message sanitization

Data Privacy
├─ No persistent document storage
├─ Session-based state only
├─ LLM API keys in environment variables
└─ No logs containing sensitive data
```

---

**Architecture Version**: 1.0  
**Last Updated**: January 26, 2026  
**Status**: ✅ Production Ready
