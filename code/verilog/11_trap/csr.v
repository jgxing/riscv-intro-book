module csr (
    input  wire        clk,
    input  wire        rst_n,

    input  wire [11:0] csr_addr_i,
    input  wire [31:0] csr_wdata_i,
    input  wire        csr_we_i,
    output wire [31:0] csr_rdata_o,

    input  wire        trap_i,
    input  wire [31:0] trap_cause_i,
    input  wire [31:0] trap_epc_i,
    input  wire [31:0] trap_val_i,
    input  wire [31:0] mstatus_trap_i,

    input  wire        mret_i,
    input  wire [31:0] mstatus_mret_i,

    input  wire        irq_i,

    output wire [31:0] mstatus_o,
    output wire [31:0] mie_o,
    output wire [31:0] mtvec_o,
    output wire [31:0] mepc_o,
    output wire [31:0] mcause_o,
    output wire [31:0] mtval_o
);

    localparam [11:0] CSR_MSTATUS = 12'h300;
    localparam [11:0] CSR_MIE     = 12'h304;
    localparam [11:0] CSR_MTVEC   = 12'h305;
    localparam [11:0] CSR_MEPC    = 12'h341;
    localparam [11:0] CSR_MCAUSE  = 12'h342;
    localparam [11:0] CSR_MTVAL   = 12'h343;
    localparam [11:0] CSR_MIP     = 12'h344;

    reg [31:0] mstatus;
    reg [31:0] mie;
    reg [31:0] mtvec;
    reg [31:0] mepc;
    reg [31:0] mcause;
    reg [31:0] mtval;

    wire [31:0] mip = {20'b0, irq_i, 11'b0};

    assign mstatus_o = mstatus;
    assign mie_o     = mie;
    assign mtvec_o   = mtvec;
    assign mepc_o    = mepc;
    assign mcause_o  = mcause;
    assign mtval_o   = mtval;

    reg [31:0] rdata_r;
    always @(*) begin
        case (csr_addr_i)
            CSR_MSTATUS: rdata_r = mstatus;
            CSR_MIE:     rdata_r = mie;
            CSR_MTVEC:   rdata_r = mtvec;
            CSR_MEPC:    rdata_r = mepc;
            CSR_MCAUSE:  rdata_r = mcause;
            CSR_MTVAL:   rdata_r = mtval;
            CSR_MIP:     rdata_r = mip;
            default:     rdata_r = 32'b0;
        endcase
    end
    assign csr_rdata_o = rdata_r;

    always @(posedge clk) begin
        if (!rst_n) begin
            mstatus <= 32'b0;
            mie     <= 32'b0;
            mtvec   <= 32'b0;
            mepc    <= 32'b0;
            mcause  <= 32'b0;
            mtval   <= 32'b0;
        end else begin
            if (csr_we_i) begin
                case (csr_addr_i)
                    CSR_MSTATUS: mstatus <= csr_wdata_i;
                    CSR_MIE:     mie     <= csr_wdata_i;
                    CSR_MTVEC:   mtvec   <= {csr_wdata_i[31:2], 2'b00};
                    CSR_MEPC:    mepc    <= {csr_wdata_i[31:2], 2'b00};
                    CSR_MCAUSE:  mcause  <= csr_wdata_i;
                    CSR_MTVAL:   mtval   <= csr_wdata_i;
                    default:     ;
                endcase
            end
            if (trap_i) begin
                mepc    <= trap_epc_i;
                mcause  <= trap_cause_i;
                mtval   <= trap_val_i;
                mstatus <= mstatus_trap_i;
            end
            if (mret_i) begin
                mstatus <= mstatus_mret_i;
            end
        end
    end

endmodule
