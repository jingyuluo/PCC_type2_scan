import sys, os
from math import exp,fabs
import argparse
import subprocess
from array import array

ROOTSYS='/Users/jingyuluo/Downloads/Program/root/lib'
sys.path.append(ROOTSYS)

import ROOT
from ROOT import TGraph2D

parser=argparse.ArgumentParser()
#parser.add_argument("-h", "--help", help="Display this message.")
parser.add_argument("-p", "--path", default="", help="The path to the output correciton files")
parser.add_argument("-n", "--name", default="After_Corr", help="The name of histogram that need to be checked")
parser.add_argument("-r", "--run", default="", help="The run number to be checked")
parser.add_argument("-l", "--label", default="", help="The label for outputs")
parser.add_argument("-b", "--batch", action='store_true', default=False, help="Batch mode (doesn't make GUI TCanvases)")
parser.add_argument("-c", "--cut", default="30", help="The number of bins cut for the long tail after a bunch train when calulating the Chi2s")
parser.add_argument("--sa", default=False, action='store_true', help="Do the 2d slice when fix a in the 3d scan")
parser.add_argument("--sb", default=False, action='store_true', help="Do the 2d slice when fix b in the 3d scan")
parser.add_argument("--sc", default=False, action='store_true', help="Do the 2d slice when fix c in the 3d scan")
parser.add_argument("--value", default="0", help="The value of the parameter for slice in 3d scan")
parser.add_argument("-q","--qsquare", default=False, action='store_true', help="Using the Chi2 to do the minimization, default is standard deviation") 

args=parser.parse_args()


value = float(args.value)

ROOT.gStyle.SetOptStat(0)
if args.batch is True:
    ROOT.gROOT.SetBatch(ROOT.kTRUE)

histname= args.name
run_num = args.run
cut_value = int(args.cut)

a_array = array('d')
b_array = array('d')
c_array = array('d')

chi2type1_array = array('d')
chi2overall_array = array('d')
chi2train_array = array('d')
chi2tail_array = array('d')
chi2combine_array = array('d')

outfile=ROOT.TFile("Grid_Chi2_"+args.run+"_"+args.cut+"_"+args.path+"_"+args.label+".root", "recreate")

files=os.listdir(args.path)
files.sort()

min_chi2type1=1e20
min_chi2overall=1e20
min_chi2train=1e20
min_chi2tail=1e20
min_chi2combine=1e20


min_a_type1=0
min_b_type1=0
min_c_type1=0

min_a_overall=0
min_b_overall=0
min_c_overall=0

min_a_train=0
min_b_train=0
min_c_train=0

min_a_tail=0
min_b_tail=0
min_c_tail=0

min_a_combine=0
min_b_combine=0
min_c_combine=0

for filename in files:
    tfile=ROOT.TFile(args.path+"/"+filename)
    histpar_a = tfile.Get("Parameter_a1")
    histpar_b = tfile.Get("Parameter_b")
    histpar_c = tfile.Get("Parameter_c")

    a = histpar_a.GetBinContent(4)
    b = histpar_b.GetBinContent(4)
    c = histpar_c.GetBinContent(4)


    print "Parameter a:  ", a
    print "Parameter b:  ", b
    print "Parameter c:  ", c

    if args.sa:
        if (fabs(a-value)>0.0009):
            continue
    
    if args.sb:
        if (fabs(b-value)>0.000009):
            continue
   
    if args.sc:
        if (fabs(c-value)>0.0009):
            continue


    hist_tocheck = tfile.Get(histname)

    maxi=hist_tocheck.GetMaximum()

    nonlumi_list=[]
    dist_list=[]   # The distance between the nonlumi BX and the closest active BX before it
    flag_train_list=[] # Whether the nonlumi BX is within a Bunch train

    first_actBX=False  # Whether the BX is behind the first active BX
    dist=-1

    for i in range(hist_tocheck.GetNbinsX()):

        if not first_actBX:
            if hist_tocheck.GetBinContent(i)>0.2*maxi:
                dist=0
                first_actBX=True
            continue

        if hist_tocheck.GetBinContent(i)>0.2*maxi:
            dist=0
        else:
            dist+=1
            nonlumi_list.append(i)
            dist_list.append(dist)
            
            if dist==1 and hist_tocheck.GetBinContent(i+1)>0.2*maxi:
                flag_train_list.append(True)
            else:
                flag_train_list.append(False)
            #if dist>=1:
            #    nonlumi_list.append(i)
            #    dist_list.append(dist)
            #dist+=1

            #if dist==1 and hist_tocheck.GetBinContent(i+1)>0.2*maxi:
            #    flag_train_list.append(True)
            #else:
            #    flag_train_list.append(False)


    Chi2_type1=0
    Chi2_Overall=0 # The Chi2 based on all the non-lumi BXs
    Chi2_Train=0 # The Chi2 only based on the non-lumi BXs within a bunch train
    Chi2_Tail=0 # The Chi2 only based on the long tail after a bunch train (with the Bin number cut)
    Chi2_combine=0 # The Chi2 based on both the non-lumi BXs within bunch trains and the long tail after bunch trains

    Sum_type1=0
    Sum_Overall = 0
    Sum_Train = 0
    Sum_Tail = 0
    Sum_combine = 0

    N_type1=0
    N_Overall = 0
    N_Train = 0
    N_Tail = 0
    N_combine = 0

    for j in range(len(nonlumi_list)):
        Chi2_Overall+=hist_tocheck.GetBinContent(nonlumi_list[j])*hist_tocheck.GetBinContent(nonlumi_list[j])
        Sum_Overall+=hist_tocheck.GetBinContent(nonlumi_list[j])
        N_Overall+=1
        
        if dist_list[j]==1 and dist_list[j+1]==2:
            Chi2_type1+=(hist_tocheck.GetBinContent(nonlumi_list[j])-hist_tocheck.GetBinContent(nonlumi_list[j+1]))*(hist_tocheck.GetBinContent(nonlumi_list[j])-hist_tocheck.GetBinContent(nonlumi_list[j+1]))
            N_type1+=1

        if flag_train_list[j]:
            Chi2_Train+=hist_tocheck.GetBinContent(nonlumi_list[j])*hist_tocheck.GetBinContent(nonlumi_list[j])
            Sum_Train+=hist_tocheck.GetBinContent(nonlumi_list[j])
            N_Train+=1
        elif dist_list[j]<cut_value and dist_list[j]>5:
            Chi2_Tail+=hist_tocheck.GetBinContent(nonlumi_list[j])*hist_tocheck.GetBinContent(nonlumi_list[j])
            Sum_Tail+=hist_tocheck.GetBinContent(nonlumi_list[j])
            N_Tail+=1
        

        if dist_list[j]<cut_value:
            Chi2_combine+=hist_tocheck.GetBinContent(nonlumi_list[j])*hist_tocheck.GetBinContent(nonlumi_list[j])
            Sum_combine+=hist_tocheck.GetBinContent(nonlumi_list[j])
            N_combine+=1

    Chi2_type1=Chi2_type1/N_type1

    if not args.qsquare:
        Chi2_Overall = Chi2_Overall/N_Overall-(Sum_Overall*Sum_Overall)/N_Overall/N_Overall
        if not N_Train==0:
            Chi2_Train = Chi2_Train/N_Train - (Sum_Train*Sum_Train)/N_Train/N_Train
        print "Test:", Chi2_Tail/N_Tail
        Chi2_Tail = Chi2_Tail/N_Tail - (Sum_Tail*Sum_Tail)/N_Tail/N_Tail
        print N_Tail, Chi2_Tail, Sum_Tail
        Chi2_combine = Chi2_combine/N_combine - (Sum_combine*Sum_combine)/N_combine/N_combine
    else:
        Chi2_Overall= Chi2_Overall/N_Overall
        if not N_Train==0:
            Chi2_Train = Chi2_Train/N_Train
        Chi2_Tail = Chi2_Tail/N_Tail
        Chi2_combine = Chi2_combine/N_combine
    print "Chi2_type1: ", Chi2_type1
    print "Chi2_Overall: ", Chi2_Overall
    print "Chi2_Train:   ", Chi2_Train
    print "Chi2_Tail:    ", Chi2_Tail
    print "Chi2_combine: ", Chi2_combine

    a_array.append(a)
    b_array.append(b)
    c_array.append(c)

    if Chi2_type1 < min_chi2type1:
        min_chi2type1 = Chi2_type1
        min_a_type1 = a
        min_b_type1 = b
        min_c_type1 = c

    if Chi2_Overall < min_chi2overall:
        min_chi2overall = Chi2_Overall
        min_a_overall = a
        min_b_overall = b
        min_c_overall = c
   
    if Chi2_Train < min_chi2train:
        min_chi2train = Chi2_Train
        min_a_train = a
        min_b_train = b
        min_c_train = c

    if Chi2_Tail < min_chi2tail:
        min_chi2tail = Chi2_Tail
        min_a_tail = a
        min_b_tail = b
        min_c_tail = c

    if Chi2_combine < min_chi2combine:
        min_chi2combine = Chi2_combine
        min_a_combine = a
        min_b_combine = b
        min_c_combine = c

    chi2type1_array.append(Chi2_type1)
    chi2overall_array.append(Chi2_Overall)
    chi2train_array.append(Chi2_Train)
    chi2tail_array.append(Chi2_Tail)
    chi2combine_array.append(Chi2_combine)

print "Minimazation of type1 Chi2: a={0}, Chi2={1}".format(min_a_type1, min_chi2type1)
print "Minimazation of Overall Chi2: a={0}, b={1}, c={2}, Chi2={3}".format(min_a_overall, min_b_overall, min_c_overall, min_chi2overall)
print "Minimazation of Train Chi2: a={0}, b={1}, c={2}, Chi2={3}".format(min_a_train, min_b_train, min_c_train, min_chi2train)
print "Minimazation of Tail Chi2: a={0}, b={1}, c={2}, Chi2={3}".format(min_a_tail, min_b_tail, min_c_tail, min_chi2tail)
print "Minimazation of Combined Chi2: a={0}, b={1}, c={2}, Chi2={3}".format(min_a_combine, min_b_combine, min_c_combine, min_chi2combine)


grchi2type1_a = ROOT.TGraph(len(a_array), a_array, chi2type1_array)
grchi2type1_a.GetXaxis().SetTitle("a")

grchi2overall_bc = TGraph2D(len(b_array), b_array, c_array, chi2overall_array)
grchi2overall_bc.GetXaxis().SetTitle("b")
grchi2overall_bc.GetYaxis().SetTitle("c")

grchi2train_bc = TGraph2D(len(b_array), b_array, c_array, chi2train_array)
grchi2train_bc.GetXaxis().SetTitle("b")
grchi2train_bc.GetYaxis().SetTitle("c")

grchi2tail_bc = TGraph2D(len(b_array), b_array, c_array, chi2tail_array)
grchi2tail_bc.GetXaxis().SetTitle("b")
grchi2tail_bc.GetYaxis().SetTitle("c")

grchi2combine_bc = TGraph2D(len(b_array), b_array, c_array, chi2combine_array)
grchi2combine_bc.GetXaxis().SetTitle("b")
grchi2combine_bc.GetYaxis().SetTitle("c")

grchi2overall_ab = TGraph2D(len(a_array), a_array, b_array, chi2overall_array)
grchi2overall_ab.GetXaxis().SetTitle("a")
grchi2overall_ab.GetYaxis().SetTitle("b")

grchi2train_ab = TGraph2D(len(a_array), a_array, b_array, chi2train_array)
grchi2train_ab.GetXaxis().SetTitle("a")
grchi2train_ab.GetYaxis().SetTitle("b")

grchi2tail_ab = TGraph2D(len(a_array), a_array, b_array, chi2tail_array)
grchi2tail_ab.GetXaxis().SetTitle("a")
grchi2tail_ab.GetYaxis().SetTitle("b")

grchi2combine_ab = TGraph2D(len(a_array), a_array, b_array, chi2combine_array)
grchi2combine_ab.GetXaxis().SetTitle("a")
grchi2combine_ab.GetYaxis().SetTitle("b")

grchi2overall_ac = TGraph2D(len(a_array), a_array, c_array, chi2overall_array)
grchi2overall_ac.GetXaxis().SetTitle("a")
grchi2overall_ac.GetYaxis().SetTitle("c")

grchi2train_ac = TGraph2D(len(a_array), a_array, c_array, chi2train_array)
grchi2train_ac.GetXaxis().SetTitle("a")
grchi2train_ac.GetYaxis().SetTitle("c")

grchi2tail_ac = TGraph2D(len(a_array), a_array, c_array, chi2tail_array)
grchi2tail_ac.GetXaxis().SetTitle("a")
grchi2tail_ac.GetYaxis().SetTitle("c")

grchi2combine_ac = TGraph2D(len(a_array), a_array, c_array, chi2combine_array)
grchi2combine_ac.GetXaxis().SetTitle("a")
grchi2combine_ac.GetYaxis().SetTitle("c")



outfile.WriteTObject(grchi2type1_a, "grchi2type1_a")
outfile.WriteTObject(grchi2overall_bc, "grchi2overall_bc")
outfile.WriteTObject(grchi2train_bc, "grchi2train_bc")
outfile.WriteTObject(grchi2tail_bc, "grchi2tail_bc")
outfile.WriteTObject(grchi2combine_bc, "grchi2combine_bc")

outfile.WriteTObject(grchi2overall_ab, "grchi2overall_ab")
outfile.WriteTObject(grchi2train_ab, "grchi2train_ab")
outfile.WriteTObject(grchi2tail_ab, "grchi2tail_ab")
outfile.WriteTObject(grchi2combine_ab, "grchi2combine_ab")

outfile.WriteTObject(grchi2overall_ac, "grchi2overall_ac")
outfile.WriteTObject(grchi2train_ac, "grchi2train_ac")
outfile.WriteTObject(grchi2tail_ac, "grchi2tail_ac")
outfile.WriteTObject(grchi2combine_ac, "grchi2combine_ac")

outfile.Close()


