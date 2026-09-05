module.exports = {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',
        accent: '#6366F1',
        slatey: '#1E293B',
        soft: '#F8FAFC'
      },
      boxShadow: {
        soft: '0 6px 18px rgba(16,24,40,0.08)'
      }
    }
  },
  plugins: []
}
