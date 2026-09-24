import dayjs from 'dayjs'

export const localDate = () => dayjs().format('YYYY-MM-DD')
export const isFutureDate = (date: string) => dayjs(date).startOf('day').isAfter(dayjs().startOf('day'))
export const longDate = (date: string) => dayjs(date).format('MMMM D, YYYY')

export function dateInTimezone(timezone: string): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
}
