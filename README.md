# manotron

simple script that from a given path, gets all the files containing it and parses it to a sql database.

the files on this folder are suposed to be pdf scans or images from invoices.

the variation of the invoices is expected to be very light, the only tricky part is that it might contain hand writings in specific sections, specifying size of the order with hand written digits, checkmarks if it was only one, or any other classic human creative ways to mess up with the input.

initially this will be abstracted a way with a multimodal llm, by passing the image + extracted text will be asked to generate the expected schema to be put in the databse.


after that the data can be exported to a excel file in a desired format.


# features of this version
- [] easy way to install, only by bash | curl path/to/install.sh, this will register the script in the machine path and allow it to be used as a simple executable called 'manotron' or 'salidas' im not sure yet. target OS macOS with arm
- [] during the installation will be asked to provided an openai api key (or equivalent) and check its validity, stopping installation if its not valid.
- [] during onboarding/installation will be asked to register a folder. all of this can be changed later with config flags.
- [] register a sqlite db to track the total current orders.
- [] option flag to export the data from the local sql to a excel, can sprcify path and date range, if nothing specificed and only export, it will create an excel with the datetime with every inside the db.
- [] app is executable as somthing you can click, this might be done just by wrapping the command call. no fancy ui for now.
- [] it will check to not duplacate data entries. first filter is done by file data (name / updated at / created at ) then after extracting the invoice data, will be compared against the current status to double check.

## schema
each row will have:
- invoice reference id : str
- invoice date : datetime
- product reference id : str
- product locations : str
- quantity deducted : int
- locations quantity: str -> (location)::amount;(location)::amount;....


### dev notes

considerations

- pyinstaller to convert to executable seems good
- python because easy
- openai client with structured outputs defined with pydantic because have tried and is good.
- input is either image or pdf, consider this for ai client
- retrieve and write from sqlite, compare this to extracted data from invoice
- clean design, first define parameters of the script, then models, clean and simple functions, and execution flow parsing errors form one to other.
- the place where the install sh will be served from this repo so we ahve to use some those rawgithub links, as well as pushing the executable in this repo



