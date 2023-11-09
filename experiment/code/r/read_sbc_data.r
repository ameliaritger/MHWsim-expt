# this code is a function that used to read the data from the SBC data package
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

dt <- read.csv("vw_timeseries_entities.csv",stringsAsFactors = FALSE)

read_sbc_data<-function(namein)
{
 # namein = "Nearshore CTD and Rosette Bottle Profiles - Monthly bottle chemistry with CTD, registered stations, all years"
sel <- dt %>% 
  filter(dsname == namein) %>% 
  select(identifier,entityorder)

scope = "knb-lter-sbc"
identifier = sel$identifier[1]
revision = list_data_package_revisions(scope, identifier, filter = "newest")
packageid <- paste(scope, identifier, revision, sep = ".")

#transaction <- create_data_package_archive(packageid)

#read_data_package_archive(packageid, transaction, path = tempdir())

#dir(tempdir())

res <- read_data_entity_names(packageid)

entityid <- res$entityId[sel$entityorder[1]]

raw <- read_data_entity(packageid, entityid)

eml <- read_metadata(packageid)
meta <- read_metadata_entity(packageid, entityid)
fieldDelimiter <- xml_text(xml_find_first(meta, ".//physical//fieldDelimiter"))
numHeaderLines <- xml_double(xml_find_first(meta, ".//physical//numHeaderLines"))

# extract a list of missing value code
missingValueCode <- unique(xml_text(xml_find_all(meta, ".//attributeList//attribute//missingValueCode//code")))

# use maximum number of line to guess the column type
maxLine <- 3000

data <- readr::read_delim(
  file = raw, 
  delim = fieldDelimiter, 
  skip = numHeaderLines-1,
  na = missingValueCode,
  guess_max = maxLine,
  show_col_types = FALSE)

return(data)
}
