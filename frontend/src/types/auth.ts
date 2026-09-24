export interface User {
  id: string
  username: string
}

export interface ApiError {
  code: string
  message: string
  details: unknown
}

