# Use cases: financial controller, laboratory, regulator, and signing

## UC-15. Exporting the financial summary of acts

**Role.** Financial controller.

**Goal.** Obtain summary figures from signed acts, to pass to the finance systems
for billing and settlement.

**Precondition.** Transfer acts have been signed by the parties.

**Main scenario**

1. The controller opens the financial summary section.
2. The controller selects a period, a month or a quarter.
3. The system gathers the data from the acts signed in that period: total volumes
   per line and per act, aggregated quality figures, and the dates the acts were
   signed.
4. The controller picks the export format, a structured file or an API response.
5. The system produces the file for download.

**Result.** The controller has structured data to pass to the finance system.

**Alternatives**

- Some acts in the period are unsigned: the system includes them marked "not
  signed".
- The controller asks for a summary for one counterparty: the system filters to
  that counterparty.

## UC-23. Uploading chromatography results

**Role.** Laboratory technician.

**Goal.** Enter gas composition analysis results into the system, for use in
calculations.

**Precondition.** The technician is signed in.

**Main scenario**

1. The technician opens the chromatogram entry section.
2. The technician selects the metering node the sample belongs to.
3. The technician states the date and time the sample was taken — the period the
   composition applies to.
4. The technician uploads the results file or enters the data by hand.
5. The system validates the data: format, value ranges, and that the components
   sum to 100%.
6. The system stores the data and notifies the accounting engineer that a new
   chromatogram has arrived, so the calculation can run.

**Result.** The gas composition is loaded and ready for use in calculations.

**Alternatives**

- The data fails validation: the system shows the error and the technician
  corrects and re-uploads.
- The data is loaded but its period is already closed: the system accepts it and
  marks it "requires a corrective act".

## UC-24. Exporting the full data set for audit

**Role.** Regulator or external auditor.

**Goal.** Obtain the full data set for an arbitrary period on request, to verify
that the calculations are correct.

**Precondition.** The regulator is signed in.

**Main scenario**

1. The regulator opens the audit export section.
2. The regulator selects a period, as a date range.
3. The regulator selects metering nodes, or leaves "all".
4. The regulator presses "produce export".
5. The system gathers, for that period: raw measurements from the operational
   layer; corrected volumes from the accounting layer; the method versions
   applied, with their effective dates; the complete correction journal; every
   act produced, original and corrective; and the technical information needed
   for reproducibility — calculation identifiers and the identifiers of the
   method reference versions applied. Reproducibility rests on a fixed
   calculation algorithm together with the versioned reference data in force at
   the time of calculation.
6. The system produces an archive for download.
7. The system records the export itself, with the date and the user, in a
   separate store.

**Result.** The regulator has a full export for an independent audit.

**Alternatives**

- The data set is too large: the system produces the export in parts, or notifies
  the regulator when it is ready.
- The regulator asks for a period that is not fully calculated: the system
  exports what is available and marks the rest.
- The data is needed in machine-readable form for loading into other software:
  the system exports in a structured format — JSON, XML, CSV — matching the
  regulator's requirements where these are known and covered by the MVP.

## UC-25. Signing the transfer act

**Roles.** Accounting engineer and counterparty representative.

**Goal.** Record both parties' agreement with the calculated volumes, by signing
the act on both sides.

**Precondition.** The act has been produced and is in "ready for signing" status;
the user is signed in.

**Main scenario**

1. The system notifies both parties that the act is ready for signing.
2. The accounting engineer opens the act and reviews the totals and the breakdown
   by node.
3. The accounting engineer signs; the system records the signature with the party
   (operator), the user and the time.
4. The counterparty representative opens the act and checks the volumes against
   their own data.
5. The counterparty representative signs; the system records the signature with
   the party (counterparty), the user and the time.
6. Once both signatures are present, the system moves the act to "signed".
7. The system starts the T + 10 working day count from the end of the reporting
   period.

**Result.** The act is signed by both parties and the period awaits closing.

**Alternatives**

- The counterparty disagrees with the volumes: they raise a protocol of
  disagreement instead of signing; the act does not move to "signed" and the
  process passes to dispute resolution.
- A user tries to sign an act for a delivery point they have no access to: the
  system rejects the action and reports the missing right.
- A party signs an act it has already signed: the system rejects the action and
  reports that this party's signature is already recorded.
- Signing is attempted after the period has closed, T + 10 having passed: the
  system blocks it and reports that the period is closed.

**Note.** Signing is a parallel process. Both parties sign independently, the
system imposes no order, and it waits for both signatures before moving the act
to its final status. This matches the BPMN process "producing and signing the
act" and the endpoint `POST /acts/{actId}/signatures`.
