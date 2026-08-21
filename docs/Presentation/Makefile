# simTIM -- ARES 2026 talk
#
#   make          talk deck        -> simTIM_ARES26_slides.pdf
#                 + Q&A backup deck -> simTIM_ARES26_backup.pdf
#   make backup   backup deck only
#   make notes    talk + speaker notes side by side -> ..._notes.pdf
#   make figures  regenerate the violin plot from a real simTIM run
#   make clean

DECK    := simTIM_ARES26_slides
BACKUP  := simTIM_ARES26_backup
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: all backup notes figures clean

all: $(DECK).pdf $(BACKUP).pdf

$(DECK).pdf: $(DECK).tex preamble.tex figures/violin_defense_duration.pdf
	$(LATEXMK) $(DECK).tex

backup: $(BACKUP).pdf

$(BACKUP).pdf: $(BACKUP).tex backup_slides.tex preamble.tex
	$(LATEXMK) $(BACKUP).tex

notes:
	$(LATEXMK) -jobname=$(DECK)_notes \
	  -pretex='\def\notesversion{}' -usepretex $(DECK).tex

figures:
	cd ../.. && python docs/Presentation/make_figures.py

clean:
	latexmk -C $(DECK).tex $(BACKUP).tex
	rm -f $(DECK)_notes.* *.nav *.snm *.vrb
