//`include "/cad/eda/cadence/INCISIV/15.20.036/linux_i/tools.lnx86/affirma_ams/etc/dms/EE_pkg.sv"
import EE_pkg::*;

typedef struct {
    real i;
    real m;
}  mystruct;

nettype mystruct mynet;


module top;

    reg [31:0]    a;
    reg [31:0]    b;
    reg [31:0]    c;
    EEnet         p;
	reg 		  clk;

    initial begin
        a = 0;
        b = 0;
    end

   initial begin
	clk = 0;
    #100;
	forever begin
	   #(1us) clk = ~clk;
	end	   
   end

endmodule
