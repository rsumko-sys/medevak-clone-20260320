import { BodyRegion, InjuryType } from './types'

export const INJURY_ICONS: Record<InjuryType, string> = {
  ENTRY_WOUND: '•',
  EXIT_WOUND: '◦',
  FRAG_WOUND: '×',
  MASSIVE_BLEEDING: '▼',
  BLEEDING: '▽',
  BURN: '~',
  AMPUTATION: '✕',
  OPEN_WOUND: '—',
  FRACTURE_SUSPECTED: '≈',
  BRUISE_CONTUSION: '●',
  BLAST_INJURY: '◎',
  CHEST_WOUND: '+',
  PNEUMOTHORAX_SUSPECTED: '?',
  OTHER: '?'
}

export interface BodyZone {
  id: BodyRegion
  name: string
  view: 'front' | 'back' | 'both'
  protocol?: 'M' | 'A' | 'R' | 'C'
  x: number
  y: number
  w: number
  h: number
}

export const BODY_ZONES: BodyZone[] = [
  { id: 'HEAD', name: 'Голова', view: 'both', protocol: 'A', x: 40, y: 4, w: 20, h: 8 },
  { id: 'FACE', name: 'Обличчя', view: 'front', protocol: 'A', x: 40, y: 12, w: 20, h: 8 },
  { id: 'NECK', name: 'Шия', view: 'both', protocol: 'A', x: 40, y: 20, w: 20, h: 8 },

  { id: 'CHEST_LEFT_ANT', name: 'Груди Л (перед)', view: 'front', protocol: 'R', x: 32, y: 28, w: 12, h: 12 },
  { id: 'CHEST_CENTER_ANT', name: 'Груди Ц (перед)', view: 'front', protocol: 'R', x: 44, y: 28, w: 12, h: 12 },
  { id: 'CHEST_RIGHT_ANT', name: 'Груди П (перед)', view: 'front', protocol: 'R', x: 56, y: 28, w: 12, h: 12 },
  { id: 'CHEST_ANTERIOR', name: 'Грудна клітка (перед)', view: 'front', protocol: 'R', x: 44, y: 28, w: 24, h: 12 },

  { id: 'CHEST_LEFT_POST', name: 'Груди Л (тил)', view: 'back', protocol: 'R', x: 32, y: 28, w: 12, h: 12 },
  { id: 'CHEST_CENTER_POST', name: 'Груди Ц (тил)', view: 'back', protocol: 'R', x: 44, y: 28, w: 12, h: 12 },
  { id: 'CHEST_RIGHT_POST', name: 'Груди П (тил)', view: 'back', protocol: 'R', x: 56, y: 28, w: 12, h: 12 },
  { id: 'CHEST_POSTERIOR', name: 'Грудна клітка (тил)', view: 'back', protocol: 'R', x: 44, y: 28, w: 24, h: 12 },

  { id: 'ABDOMEN_LEFT', name: 'Живіт Л', view: 'front', protocol: 'C', x: 38, y: 40, w: 14, h: 10 },
  { id: 'ABDOMEN_RIGHT', name: 'Живіт П', view: 'front', protocol: 'C', x: 52, y: 40, w: 14, h: 10 },
  { id: 'ABDOMEN', name: 'Живіт', view: 'front', protocol: 'C', x: 45, y: 40, w: 20, h: 10 },

  { id: 'BACK_UPPER_LEFT', name: 'Спина верх Л', view: 'back', protocol: 'C', x: 38, y: 40, w: 14, h: 10 },
  { id: 'BACK_UPPER_RIGHT', name: 'Спина верх П', view: 'back', protocol: 'C', x: 52, y: 40, w: 14, h: 10 },
  { id: 'BACK_LOWER_LEFT', name: 'Поперек Л', view: 'back', protocol: 'C', x: 38, y: 50, w: 14, h: 10 },
  { id: 'BACK_LOWER_RIGHT', name: 'Поперек П', view: 'back', protocol: 'C', x: 52, y: 50, w: 14, h: 10 },
  { id: 'BACK', name: 'Спина', view: 'back', protocol: 'C', x: 45, y: 45, w: 20, h: 14 },
  { id: 'SPINE', name: 'Хребет', view: 'back', protocol: 'C', x: 47, y: 28, w: 6, h: 32 },

  { id: 'PELVIS_LEFT', name: 'Таз Л', view: 'both', protocol: 'C', x: 40, y: 60, w: 12, h: 8 },
  { id: 'PELVIS_RIGHT', name: 'Таз П', view: 'both', protocol: 'C', x: 52, y: 60, w: 12, h: 8 },
  { id: 'PELVIS', name: 'Таз', view: 'both', protocol: 'C', x: 44, y: 60, w: 20, h: 8 },

  { id: 'L_SHOULDER', name: 'Л плече', view: 'both', protocol: 'M', x: 70, y: 28, w: 10, h: 8 },
  { id: 'L_UPPER_ARM', name: 'Л плече (верх)', view: 'both', protocol: 'M', x: 72, y: 36, w: 10, h: 10 },
  { id: 'L_ELBOW', name: 'Л лікоть', view: 'both', protocol: 'M', x: 74, y: 46, w: 8, h: 8 },
  { id: 'L_FOREARM', name: 'Л передпліччя', view: 'both', protocol: 'M', x: 74, y: 54, w: 8, h: 10 },
  { id: 'L_WRIST', name: 'Л запʼястя', view: 'both', protocol: 'M', x: 75, y: 64, w: 7, h: 6 },
  { id: 'L_HAND', name: 'Л кисть', view: 'both', protocol: 'M', x: 75, y: 70, w: 7, h: 8 },

  { id: 'R_SHOULDER', name: 'П плече', view: 'both', protocol: 'M', x: 20, y: 28, w: 10, h: 8 },
  { id: 'R_UPPER_ARM', name: 'П плече (верх)', view: 'both', protocol: 'M', x: 18, y: 36, w: 10, h: 10 },
  { id: 'R_ELBOW', name: 'П лікоть', view: 'both', protocol: 'M', x: 18, y: 46, w: 8, h: 8 },
  { id: 'R_FOREARM', name: 'П передпліччя', view: 'both', protocol: 'M', x: 18, y: 54, w: 8, h: 10 },
  { id: 'R_WRIST', name: 'П запʼястя', view: 'both', protocol: 'M', x: 18, y: 64, w: 7, h: 6 },
  { id: 'R_HAND', name: 'П кисть', view: 'both', protocol: 'M', x: 18, y: 70, w: 7, h: 8 },

  { id: 'L_THIGH', name: 'Л стегно', view: 'both', protocol: 'M', x: 52, y: 68, w: 12, h: 12 },
  { id: 'L_KNEE', name: 'Л коліно', view: 'both', protocol: 'M', x: 54, y: 80, w: 8, h: 8 },
  { id: 'L_LOWER_LEG', name: 'Л гомілка', view: 'both', protocol: 'M', x: 53, y: 88, w: 10, h: 12 },
  { id: 'L_ANKLE', name: 'Л кісточка', view: 'both', protocol: 'M', x: 54, y: 100, w: 8, h: 6 },
  { id: 'L_FOOT', name: 'Л стопа', view: 'both', protocol: 'M', x: 53, y: 106, w: 10, h: 8 },

  { id: 'R_THIGH', name: 'П стегно', view: 'both', protocol: 'M', x: 40, y: 68, w: 12, h: 12 },
  { id: 'R_KNEE', name: 'П коліно', view: 'both', protocol: 'M', x: 42, y: 80, w: 8, h: 8 },
  { id: 'R_LOWER_LEG', name: 'П гомілка', view: 'both', protocol: 'M', x: 41, y: 88, w: 10, h: 12 },
  { id: 'R_ANKLE', name: 'П кісточка', view: 'both', protocol: 'M', x: 42, y: 100, w: 8, h: 6 },
  { id: 'R_FOOT', name: 'П стопа', view: 'both', protocol: 'M', x: 41, y: 106, w: 10, h: 8 }
]
