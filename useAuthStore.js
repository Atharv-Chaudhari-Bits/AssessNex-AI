import create from 'zustand'

const useAuthStore = create((set) => ({
  token: null,
  user: null,
  loading: false,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  updateProfile: (patch) => set((state) => ({ user: { ...(state.user||{}), ...patch } })),
  logout: () => {
    set({ token: null, user: null })
    localStorage.removeItem('assessnex_auth')
  },
  saveToStorage: (token, user) => {
    localStorage.setItem('assessnex_auth', JSON.stringify({ token, user }))
    set({ token, user })
  },
  loadFromStorage: () => {
    try{
      const raw = localStorage.getItem('assessnex_auth')
      if(raw){
        const { token, user } = JSON.parse(raw)
        set({ token, user })
      }
    }catch(e){ }
  }
}))

export default useAuthStore
