// Free numbers a farmer can call, in one place so the shown number and the dialled number can't drift.

export interface Helpline {
  display: string; // as printed for the farmer
  tel: string; // what the phone dials
  source: string;
}

/** Kisan Call Centre: free, 6 am–10 pm, Telugu spoken. */
export const KISAN_CALL_CENTRE: Helpline = {
  display: "1800-180-1551",
  tel: "tel:18001801551",
  source: "https://mkisan.gov.in/Home/AboutKCC",
};

/** National cyber-crime helpline: call at once after a fraud — money can still be stopped early. */
export const CYBER_CRIME: Helpline = {
  display: "1930",
  tel: "tel:1930",
  source: "https://cybercrime.gov.in",
};

export const CYBER_CRIME_PORTAL = "https://cybercrime.gov.in";
