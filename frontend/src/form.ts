// Bundled at build time so the walkthrough works even while the free-tier backend is asleep.
import schema from '../../backend/app/forms/anmeldung.json'
import type { FormSchema } from './types'

export const form = schema as FormSchema
